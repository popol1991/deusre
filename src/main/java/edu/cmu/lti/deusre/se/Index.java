package edu.cmu.lti.deusre.se;

import java.util.HashMap;
import java.util.Map;

/**
 * Created by Kyle on 2/4/15.
 */
public abstract class Index {
    public abstract boolean create(Map<String, String> settings, boolean recreate);
    public abstract void addDoc(Map<String, String> doc);
    public abstract void close();
}
