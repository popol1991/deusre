package edu.cmu.lti.deusre.index.workqueue;

import edu.cmu.lti.deusre.index.parser.Parser;
import org.json.simple.JSONObject;

import java.util.Map;

/**
 * Created by Kyle on 2/4/15.
 */
public abstract class WorkQueue {
    protected Parser parser;
    protected String dir;

    public WorkQueue(String dir, Parser parser) {
        this.dir = dir;
        this.parser = parser;
    }

    public abstract boolean hasNext();

    public abstract JSONObject[] next();
}
