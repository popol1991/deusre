package edu.cmu.lti.deusre.index.workqueue;

import edu.cmu.lti.deusre.index.parser.Parser;

import java.util.Map;

/**
 * Created by Kyle on 2/4/15.
 */
public abstract class WorkQueue {
    private Parser parser;

    public WorkQueue(Parser parser) {
        this.parser = parser;
    }

    public abstract boolean hasNext();

    public abstract Map<String,String> next();
}
