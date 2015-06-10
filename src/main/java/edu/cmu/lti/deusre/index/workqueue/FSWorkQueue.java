package edu.cmu.lti.deusre.index.workqueue;

import edu.cmu.lti.deusre.index.parser.Parser;
import org.apache.commons.io.FilenameUtils;
import org.json.simple.JSONObject;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Iterator;
import java.util.stream.Stream;

/**
 * Created by Kyle on 2/4/15.
 */
public class FSWorkQueue extends WorkQueue {
    private Iterator<Path> iterator;
    private Path next;
    private String extension;

    public FSWorkQueue(String dir, Parser parser) {
        super(dir, parser);
        this.extension = parser.getExtension();
        Path path = Paths.get(dir);
        try {
            Stream<Path> pathStream = Files.walk(path);
            this.iterator = pathStream.iterator();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    @Override
    public boolean hasNext() {
        next = null;
        while (iterator.hasNext()) {
            next = iterator.next();
            String ext = FilenameUtils.getExtension(next.toString());
            if (ext.equals(extension)) {
                break;
            }
        }
        return next != null;
    }

    @Override
    public JSONObject[] next() {
        JSONObject[] ret = null;
        try {
            ret = parser.parse(next);
        } finally {
            return ret;
        }
    }
}
