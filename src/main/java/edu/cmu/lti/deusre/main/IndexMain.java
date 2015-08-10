package edu.cmu.lti.deusre.main;

import edu.cmu.lti.deusre.index.parser.Parser;
import edu.cmu.lti.deusre.index.parser.XMLParser;
import edu.cmu.lti.deusre.index.workqueue.FSWorkQueue;
import edu.cmu.lti.deusre.index.workqueue.WorkQueue;
import edu.cmu.lti.deusre.se.ElasticSearchIndex;
import edu.cmu.lti.deusre.se.Index;
import org.apache.commons.io.FilenameUtils;
import org.json.simple.JSONObject;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;
import java.util.Properties;
import java.util.Scanner;
import java.util.stream.Collectors;

/**
 * Created by Kyle on 2/4/15.
 */
public class IndexMain {
    public static final String CONFIG_PATH = "config.properties";

    public static HashMap<String, Long> IDMap;

    public static void main(String[] args) throws IOException {
        Properties config = readConfig(CONFIG_PATH);
        // initialization
        Index index = initIndexServer(config);
        Parser parser = new XMLParser();
        String dir = config.getProperty("data");
        WorkQueue wq = new FSWorkQueue(dir, parser);
        IDMap = initIDMap(config.getProperty("id_map"));
        while (wq.hasNext()) {
            JSONObject[] docList = wq.next();
            if (docList == null) continue;
            int tableId = 0;
            for (Map<String, String> doc : docList) {
                String pathAsId = doc.get("path");
//                String id = pathAsId + "." + tableId;
                long internal = getInternalId(pathAsId);
                if (internal != -1) {
                    String id = String.format("%d%02d", internal, tableId);
                    tableId++;
                    doc.put("id", id);
                    index.addDoc(doc);
                }
            }
        }
        index.close();
    }

    private static HashMap<String,Long> initIDMap(String path) throws FileNotFoundException {
        HashMap<String, Long> retMap = new HashMap<>();
        Scanner sc = new Scanner(new File(path));
        while (sc.hasNextLine()) {
            String line = sc.nextLine();
            String[] ids = line.split(",");
            retMap.put(ids[0], Long.parseLong(ids[2]));
        }
        sc.close();
        return retMap;
    }

    private static long getInternalId(String path) {
        String filename = FilenameUtils.getName(path);
        long internalId = 0;
        try {
            internalId = IDMap.get(filename);
        } catch (NullPointerException e) {
            return -1;
        }
        return internalId;
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
