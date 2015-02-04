package edu.cmu.lti.deusre.main;

import edu.cmu.lti.deusre.index.parser.Parser;
import edu.cmu.lti.deusre.index.parser.XMLParser;
import edu.cmu.lti.deusre.index.workqueue.FSWorkQueue;
import edu.cmu.lti.deusre.index.workqueue.WorkQueue;
import edu.cmu.lti.deusre.se.ElasticSearchIndex;
import edu.cmu.lti.deusre.se.Index;

import java.util.HashMap;

/**
 * Created by Kyle on 2/4/15.
 */
public class IndexMain {
    public static void main(String[] args) {
        // initialization
        Index index = initIndexServer();
        Parser parser = new XMLParser();
        WorkQueue wq = new FSWorkQueue(parser);
        while (wq.hasNext()) {
            index.addDoc(wq.next());
        }
        index.close();
    }

    public static Index initIndexServer() {
        Index index = new ElasticSearchIndex("localhost", "9200", "elasticsearch", "deusre");
        String settings = "";
        String mappings = "";
        HashMap<String, String> settingMap = new HashMap<>();
        settingMap.put("settings", settings);
        settingMap.put("mappings", mappings);
        index.create(settingMap, true);
        return index;
    }
}
