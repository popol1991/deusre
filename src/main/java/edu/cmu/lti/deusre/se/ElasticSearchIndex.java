package edu.cmu.lti.deusre.se;

import org.elasticsearch.action.admin.indices.create.CreateIndexRequestBuilder;
import org.elasticsearch.action.admin.indices.create.CreateIndexResponse;
import org.elasticsearch.action.admin.indices.delete.DeleteIndexRequestBuilder;
import org.elasticsearch.action.admin.indices.exists.indices.IndicesExistsResponse;
import org.elasticsearch.action.bulk.BulkRequestBuilder;
import org.elasticsearch.action.bulk.BulkResponse;
import org.elasticsearch.client.Client;
import org.elasticsearch.client.transport.TransportClient;
import org.elasticsearch.common.collect.HppcMaps;
import org.elasticsearch.common.settings.ImmutableSettings;
import org.elasticsearch.common.settings.Settings;
import org.elasticsearch.common.transport.InetSocketTransportAddress;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * Created by Kyle on 2/4/15.
 *
 * Wrapper for ElasticSearch server.
 */
public class ElasticSearchIndex extends Index {
    public static final int BULK_SIZE = 200;

    private Client client;
    private BulkRequestBuilder bulkRequest = null;

    private String indexName;
    private int docToIndex;
    private String setting;

    public ElasticSearchIndex(String host, String port, String clusterName, String indexName) {
        Settings settings = ImmutableSettings.settingsBuilder()
                .put("cluster.name", clusterName).build();
        this.client = new TransportClient(settings)
                .addTransportAddress(new InetSocketTransportAddress(host,
                        Integer.parseInt(port)));
        this.indexName = indexName;
        this.docToIndex = 0;
    }

    private void configure(Map<String, String> settings) {
        String path = settings.get("settings");
        try {
            this.setting = Files.lines(Paths.get(path)).parallel().collect(Collectors.joining());
        } catch (IOException e) {
            System.err.println("Setting file not existed, use default setting.");
        }
    }

    /**
     * Create/Open index with name and setting.
     * @param settings Settings and mappings used to create a new index.
     * @param recreate True to recreate the index if it existed.
     * @return True if successfully created, false otherwise.
     */
    @Override
    public boolean create(Map<String, String> settings, boolean recreate) {
        configure(settings);
        IndicesExistsResponse res = client.admin().indices()
                .prepareExists(indexName).execute().actionGet();
        if (recreate && res.isExists()) {
            final DeleteIndexRequestBuilder delIdx = client.admin().indices()
                    .prepareDelete(indexName);
            delIdx.execute().actionGet();
        }
        final CreateIndexRequestBuilder createIndexRequestBuilder = client
                .admin().indices().prepareCreate(indexName);
        createIndexRequestBuilder.setSettings(this.setting);
        //TODO: set mapping here?
        CreateIndexResponse createIndexResponse = createIndexRequestBuilder.execute().actionGet();
        return createIndexResponse.isAcknowledged();
    }

    /**
     * Add a document to index.  The document will not be indexed immediately
     * until the number of added documents reach the predefined size of bulk.
     * @param doc Information needed to index the document.
     *            Three string fields must be included: type, id, source.
     *            Source field must apply to ElasticSearch format.
     */
    @Override
    public void addDoc(Map<String, String> doc) {
        if (bulkRequest == null) {
            this.prepareBulk();
        }

        //this.addBulkItem(doc.get("type"), doc.get("id"), doc.get("source"));
        this.addBulkItem(doc.get("type"), doc.get("source")); // use default id to increase throughput
        docToIndex++;
        if (docToIndex == BULK_SIZE) {
            this.executeBulk();
            docToIndex = 0;
        }
    }

    @Override
    public void close() {
        // Flush left documents
        if (docToIndex != 0) {
            this.executeBulk();
        }
        client.close();
    }

    private void prepareBulk() {
        bulkRequest = client.prepareBulk();
    }

    private void addBulkItem(String type, String source) {
        bulkRequest.add(client.prepareIndex(indexName, type).setSource(source));
    }

    private void addBulkItem(String type, String id, String source) {
        bulkRequest.add(client.prepareIndex(indexName, type, id).setSource(
                source));
    }

    private void executeBulk() {
        BulkResponse res = bulkRequest.execute().actionGet();
        System.err.println(res.getItems().length + " docs indexed.");
        System.err.flush();
        if (res.hasFailures()) {
            System.err.println(res.buildFailureMessage());
        }
        this.bulkRequest = client.prepareBulk();
    }
}
