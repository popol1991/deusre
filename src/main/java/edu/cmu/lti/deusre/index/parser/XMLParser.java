package edu.cmu.lti.deusre.index.parser;

import edu.cmu.lti.huiying.features.Generator;
import opennlp.tools.sentdetect.SentenceDetectorME;
import opennlp.tools.sentdetect.SentenceModel;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.SAXException;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import javax.xml.xpath.*;
import java.io.*;
import java.nio.file.Path;
import java.util.*;

/**
 * Created by Kyle on 2/4/15.
 */
public class XMLParser extends Parser {
    private static SentenceDetectorME sdetector = null;
    public static int id = 0;

    private Generator generator;

    public XMLParser() throws IOException {
        this.extension = "xml";
        this.generator = new Generator();
        if (sdetector == null) {
            sdetector = initSentDetector();
        }
    }

    private static SentenceDetectorME initSentDetector() throws IOException {
        InputStream is = new FileInputStream("lib/en-sent.bin");
        SentenceModel model = new SentenceModel(is);
        SentenceDetectorME sdetector = new SentenceDetectorME(model);
        is.close();
        return sdetector;
    }

    @Override
    public JSONObject[] parse(Path path) {
        Document doc = getDocument(path);

        JSONObject articleInfo = getArticleInfo(doc);
        JSONObject[] tableList = getTableList(doc);
        JSONObject[] docList = new JSONObject[tableList.length];
        for (int i = 0; i < tableList.length; i++) {
            tableList[i].putAll(articleInfo);
            tableList[i].put("path", path.toString());
            docList[i] = new JSONObject();
            docList[i].put("path", path.toString());
            docList[i].put("source", tableList[i].toJSONString());
            docList[i].put("type", "table");
            docList[i].put("id", String.valueOf(id++));
        }

        return docList;
    }

    private JSONObject[] getTableList(Document doc) {
        NodeList nList = doc.getElementsByTagName("table");
        JSONObject[] retAry = new JSONObject[nList.getLength()];
        for (int i = 0; i < nList.getLength(); i++) {
            retAry[i] = getTable((Element) nList.item(i));
        }
        return retAry;
    }

    private JSONObject getTable(Element doc) {
        JSONObject retTable = new JSONObject();
        // caption
        NodeList nList = doc.getElementsByTagName("caption");
        if (nList.getLength() != 0) {
            String caption = nList.item(0).getTextContent();
            retTable.put("caption", caption);
            String[] sentences = sdetector.sentDetect(caption);
            if (sentences.length > 1) {
                String shortCap = null;
                if (sentences[0].toLowerCase().startsWith("table")) {
                    if (sentences.length > 2) {
                        shortCap = " ".join(sentences[0], sentences[1]);
                    }
                } else {
                    shortCap = sentences[0];
                }
                if (shortCap != null) {
                    retTable.put("short-caption", shortCap);
                }
            }
        }
        // footnotes
        nList = doc.getElementsByTagName("footnote");
        if (nList.getLength() > 0) {
            JSONArray fnAry = new JSONArray();
            for (int i = 0; i < nList.getLength(); i++) {
                fnAry.add(nList.item(i).getTextContent());
            }
            retTable.put("footnotes", fnAry);
        }
        // context
        nList = doc.getElementsByTagName("context");
        if (nList.getLength() > 0) {
            JSONArray headAry = new JSONArray();
            JSONArray citeAry = new JSONArray();
            for (int i = 0; i < nList.getLength(); i++) {
                XPath xpath = XPathFactory.newInstance().newXPath();
                XPathExpression headExpr = null, citationExpr = null;
                try {
                    headExpr = xpath.compile("headings/*[local-name()='section-title']");
                    Node node = (Node) headExpr.evaluate(nList.item(i), XPathConstants.NODE);
                    if (node != null) {
                        headAry.add(node.getTextContent());
                    }
                    citationExpr = xpath.compile("citation/sentence");
                    node = (Node) citationExpr.evaluate(nList.item(i), XPathConstants.NODE);
                    if (node != null) {
                        citeAry.add(node.getTextContent());
                    }
                } catch (XPathExpressionException e) {
                    e.printStackTrace();
                }
            }
            retTable.put("headings", headAry);
            retTable.put("citations", citeAry);
        }
        // headers and rows
        retTable.put("headers", getHeadersFromXml(doc, "headers", "header"));
        retTable.put("data", getDataRowsFromXml(doc));
        retTable.put("column_stats", getColumnStats(doc));
        return retTable;
    }

    private JSONObject getColumnStats(Element doc) {
        JSONObject columnStats = new JSONObject();
        NodeList nList = doc.getElementsByTagName("row");
        List<List<String>> rowList = new ArrayList<>();
        for (int i = 0; i < nList.getLength(); i++) {
            Element rowNode = (Element) nList.item(i);
            NodeList cellList = rowNode.getElementsByTagName("value");
            if (cellList.getLength() > 0) {
                List<String> row = new ArrayList<>();
                for (int j = 0; j < cellList.getLength(); j++) {
                    String text = cellList.item(j).getTextContent();
                    row.add(text);
                }
                rowList.add(row);
            }
        }
        if (rowList.size() > 0) {
            List<List<String>> columnList = getColumns(rowList);
            for (int col = 0; col < columnList.size(); col++) {
                List<String> column = columnList.get(col);
                Hashtable<String, String> features = generator.column2Vector(column);
                JSONObject colStat = new JSONObject();
                for (String key : features.keySet()) {
                    colStat.put(key, Double.parseDouble(features.get(key)));
                }
                columnStats.put("col_" + col, colStat);
            }
        }
        return columnStats;
    }

    private List<List<String>> getColumns(List<List<String>> rowList) {
        List<List<String>> columnList = new ArrayList<>();
        int width = rowList.get(0).size();
        for (List<String> row : rowList) {
            if (row.size() != width) {
                // return empty list
                return columnList;
            }
        }
        for (int col = 0; col < width; col++) {
            List<String> column = new ArrayList<>();
            for (List<String> row : rowList) {
                column.add(row.get(col));
            }
            columnList.add(column);
        }
        return columnList;
    }

    private JSONObject getDataRowsFromXml(Element doc) {
        JSONObject retRows = new JSONObject();
        NodeList nList = doc.getElementsByTagName("row");
        for (int i = 0; i < nList.getLength(); i++) {
            Element rowNode = (Element) nList.item(i);
            JSONObject dataRow = new JSONObject();
            JSONArray valueAry = new JSONArray();
            NodeList cellList = rowNode.getElementsByTagName("value");
            if (cellList.getLength() > 0) {
                // assume the first and only the first value of each data row is the row header
                dataRow.put("row_header", cellList.item(0).getTextContent());
                for (int j = 1; j < cellList.getLength(); j++) {
                    String text = cellList.item(j).getTextContent();
                    JSONObject value = new JSONObject();
                    Hashtable<String, String> features = generator.cell2Vector(text);
                    if (!features.get("type").equals("0.0")) {
                        for (String key : features.keySet()) {
                            value.put(key, Double.parseDouble(features.get(key)));
                        }
                    } else {
                        value.put("type", -1);
                    }
                    value.put("text", text);
                    valueAry.add(value);
                }
                dataRow.put("values", valueAry);
            }
            retRows.put("data_" + i, dataRow);
        }
        return retRows;
    }

    private JSONObject getHeadersFromXml(Element doc, String rowTag, String cellTag) {
        JSONObject retHeaders = new JSONObject();
        NodeList nList = doc.getElementsByTagName(rowTag);
        for (int i = 0; i < nList.getLength(); i++) {
            Element rowNode = (Element) nList.item(i);
            NodeList cellList = rowNode.getElementsByTagName(cellTag);
            for (int j = 0; j < cellList.getLength(); j++) {
                String key = "header_" + j;
                if (!retHeaders.containsKey(key)) {
                    retHeaders.put(key, new JSONArray());
                }
                Node cell = cellList.item(j);
                ((JSONArray) retHeaders.get(key)).add(cell.getTextContent());
            }
        }
        return retHeaders;
    }

    private JSONObject getArticleInfo(Document doc) {
        JSONObject articleInfo = new JSONObject();
        NodeList metaList = doc.getElementsByTagName("metadata").item(0).getChildNodes();
        for (int i = 0; i < metaList.getLength(); i++) {
            Node tag = metaList.item(i);
            String nodeName = tag.getNodeName();
            if (!nodeName.equals("#text")) {
                articleInfo.put(nodeName, tag.getTextContent());
            }
        }
        NodeList sourceList = doc.getElementsByTagName("source");
        if (sourceList.getLength() > 0) {
            Node source = sourceList.item(0);
            articleInfo.put("source", source.getTextContent());
        } else {
            articleInfo.put("source", "default");
        }
        Node title = doc.getElementsByTagName("article-title").item(0);
        articleInfo.put("article-title", title.getTextContent());
        articleInfo.put("authors", listFromXml(doc, "author"));
        articleInfo.put("keywords", listFromXml(doc, "keyword"));

//        // arXiv specific info
//        Set<String> domainSet = new HashSet<String>();
//        JSONArray subdomainAry = new JSONArray();
//        Node link = doc.getElementsByTagName("link").item(0);
//        articleInfo.put("link", link.getTextContent());
//        NodeList domainList = doc.getElementsByTagName("domain");
//        for (int i = 0; i < domainList.getLength(); i++) {
//            Node domain = domainList.item(i);
//            Element domainElm = (Element) domain;
//            NodeList subList = domainElm.getElementsByTagName("subdomain");
//            if (subList.getLength() != 0) {
//                Node subdomain = subList.item(0);
//                domain.removeChild(subdomain);
//                subdomainAry.add(String.format("%s - %s",
//                        domain.getTextContent().trim(), subdomain.getTextContent().trim()));
//            }
//            domainSet.add(domain.getTextContent().trim());
//        }
//        JSONArray domainAry = new JSONArray();
//        for (String domain : domainSet) {
//            domainAry.add(domain);
//        }
//        articleInfo.put("domains", domainAry);
//        articleInfo.put("subdomains", subdomainAry);

        return articleInfo;
    }

    private JSONArray listFromXml(Document doc, String tag) {
        JSONArray retAry = new JSONArray();
        NodeList nList = doc.getElementsByTagName(tag);
        for (int i = 0; i < nList.getLength(); i++) {
            retAry.add(nList.item(i).getTextContent().trim());
        }
        return retAry;
    }

    private Document getDocument(Path path) {
        Document doc = null;
        DocumentBuilderFactory domFactory = DocumentBuilderFactory.newInstance();
        domFactory.setNamespaceAware(true);
        try {
            DocumentBuilder builder = domFactory.newDocumentBuilder();
            File file = new File(path.toString());
            doc = builder.parse(file);
        } catch (ParserConfigurationException e) {
            e.printStackTrace();
        } catch (SAXException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }
        return doc;
    }
}
