package edu.cmu.lti.deusre.main;

import edu.cmu.lti.deusre.index.parser.Parser;
import edu.cmu.lti.deusre.index.parser.XMLParser;
import edu.cmu.lti.deusre.index.workqueue.FSWorkQueue;
import edu.cmu.lti.deusre.index.workqueue.WorkQueue;
import edu.cmu.lti.deusre.se.ElasticSearchIndex;
import edu.cmu.lti.deusre.se.Index;
import edu.cmu.lti.huiying.features.Generator;
import org.json.simple.JSONObject;

import java.util.HashMap;
import java.util.Map;

/**
 * Created by Kyle on 2/4/15.
 */
public class IndexMain {
    public static void main(String[] args) {
        if (args.length != 1) {
            System.out.println("Usage: IndexMain dataDir");
            System.exit(0);
        }
        // initialization
        Index index = initIndexServer();
        Parser parser = new XMLParser();
        String dir = args[0];
        WorkQueue wq = new FSWorkQueue(dir, parser);
        while (wq.hasNext()) {
            JSONObject[] docList = wq.next();
            for (Map<String, String> doc : docList) {
                index.addDoc(doc);
            }
        }
        index.close();
    }

    public static Index initIndexServer() {
        Index index = new ElasticSearchIndex("localhost", "9300", "experiment", "deusre");
        String settings = "";
        String mappings = "";
        HashMap<String, String> settingMap = new HashMap<>();
        settingMap.put("settings", settings);
        settingMap.put("mappings", mappings);
        index.create(settingMap, true);
        return index;
    }
}
