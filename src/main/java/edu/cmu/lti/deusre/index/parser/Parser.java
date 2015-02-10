package edu.cmu.lti.deusre.index.parser;

import org.json.simple.JSONObject;

import java.nio.file.Path;
import java.util.Map;

/**
 * Created by Kyle on 2/4/15.
 */
public abstract class Parser {
    protected String extension;

    public abstract JSONObject[] parse(Path next);
    public String getExtension() {
        return this.extension;
    }
}
