package edu.cmu.lti.deusre.index.parser;

import org.json.simple.JSONObject;

import java.nio.file.Path;
import java.util.Map;

/**
 * Created by Kyle on 2/4/15.
 */
public abstract class Parser {
    public abstract JSONObject[] parse(Path next);
}
