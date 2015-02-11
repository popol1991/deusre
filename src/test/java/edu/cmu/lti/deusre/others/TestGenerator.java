package edu.cmu.lti.deusre.others;

import edu.cmu.lti.huiying.features.Generator;
import org.junit.Before;
import org.junit.Test;

import java.util.Hashtable;

import static org.junit.Assert.assertTrue;

/**
 * Created by Kyle on 2/11/15.
 */
public class TestGenerator {
    private Generator g;

    @Before
    public void setUp() {
        this.g = new Generator();
    }

    @Test
    public void testNegative() {
        Hashtable<String, String> res = this.g.cell2Vector("−0.461");
        assertTrue(res.get("mainValue").equals("−0.461"));
    }
}
