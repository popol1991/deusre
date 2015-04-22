package edu.cmu.lti.deusre.main;

import edu.cmu.lti.deusre.index.parser.Parser;
import edu.cmu.lti.deusre.index.parser.XMLParser;
import edu.cmu.lti.deusre.index.workqueue.FSWorkQueue;
import edu.cmu.lti.deusre.index.workqueue.WorkQueue;
import edu.cmu.lti.deusre.se.ElasticSearchIndex;
import edu.cmu.lti.deusre.se.Index;
import org.json.simple.JSONObject;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;
import java.util.Properties;
import java.util.stream.Collectors;

/**
 * Created by Kyle on 2/4/15.
 */
public class IndexMain {
    public static final String CONFIG_PATH = "config.properties";

    public static void main(String[] args) {
        Properties config = readConfig(CONFIG_PATH);
        // initialization
        Index index = initIndexServer(config);
        Parser parser = new XMLParser();
        String dir = config.getProperty("data");
        WorkQueue wq = new FSWorkQueue(dir, parser);
        while (wq.hasNext()) {
            JSONObject[] docList = wq.next();
            if (docList == null) continue;
            for (Map<String, String> doc : docList) {
                index.addDoc(doc);
            }
        }
        index.close();
    }

    private static Properties readConfig(String path) {
        Properties config = new Properties();
        try {
            InputStream inStream = new FileInputStream(new File(path));
            config.load(inStream);
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }
        return config;
    }

    public static Index initIndexServer(Properties config) {
        Index index = new ElasticSearchIndex(config.getProperty("host"),
                config.getProperty("port"),
                config.getProperty("cluster"),
                config.getProperty("index"));
        HashMap<String, String> settingMap = new HashMap<>();
        settingMap.put("settings", config.getProperty("settings"));
        settingMap.put("doc_type", config.getProperty("doc_type"));
        String mappings = null;
        try {
            mappings = Files.lines(Paths.get(config.getProperty("mappings")))
                    .parallel().collect(Collectors.joining());
        } catch (IOException e) {
            e.printStackTrace();
        }
        settingMap.put("mappings", mappings);
        index.create(settingMap, true);
        return index;
    }
}
