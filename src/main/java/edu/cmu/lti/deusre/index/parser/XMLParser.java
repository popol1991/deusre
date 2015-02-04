package edu.cmu.lti.deusre.index.parser;

import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.w3c.dom.Document;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.SAXException;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import javax.xml.xpath.*;

import org.w3c.dom.Element;
import java.io.File;
import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/**
 * Created by Kyle on 2/4/15.
 */
public class XMLParser extends Parser {
    public static int id = 0;

    @Override
    public JSONObject[] parse(Path path) {
        Document doc = getDocument(path);

        JSONObject articleInfo = getArticleInfo(doc);
        JSONObject[] tableList = getTableList(doc);
        JSONObject[] docList = new JSONObject[tableList.length];
        for (int i = 0; i < tableList.length; i++) {
            tableList[i].putAll(articleInfo);
            docList[i] = new JSONObject();
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
            retTable.put("caption", nList.item(0).getTextContent());
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
        retTable.put("headers", getRowsFromXml(doc, "headers", "header"));
        retTable.put("data", getRowsFromXml(doc, "row", "value"));
        return retTable;
    }

    private JSONArray getRowsFromXml(Element doc, String rowTag, String cellTag) {
        JSONArray retRows = new JSONArray();
        NodeList nList = doc.getElementsByTagName(rowTag);
        for (int i = 0; i < nList.getLength(); i++) {
            Element rowNode = (Element) nList.item(i);
            JSONArray row = new JSONArray();
            NodeList cellList = rowNode.getElementsByTagName(cellTag);
            for (int j = 0; j < cellList.getLength(); j++) {
                Node cell = cellList.item(j);
                row.add(cell.getTextContent());
                //TODO: parse numeric value
            }
            retRows.add(row);
        }
        return retRows;
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
        Node title = doc.getElementsByTagName("article-title").item(0);
        articleInfo.put("article-title", title.getTextContent());
        articleInfo.put("authors", listFromXml(doc, "authors"));
        articleInfo.put("keywords", listFromXml(doc, "keywords"));
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
