package edu.cmu.lti.deusre.index.workqueue;

import edu.cmu.lti.deusre.index.parser.Parser;

import java.util.Map;

/**
 * Created by Kyle on 2/4/15.
 */
public class FSWorkQueue extends WorkQueue {
    public FSWorkQueue(Parser parser) {
        super(parser);
    }

    @Override
    public boolean hasNext() {
        return false;
    }

    @Override
    public Map<String, String> next() {
        return null;
    }
}
