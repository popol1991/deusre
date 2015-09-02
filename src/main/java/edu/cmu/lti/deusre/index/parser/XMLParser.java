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
    public static final String SPLIT = " $##$ ";
    public static final String NEWLINE = " #$$# ";
    public static final String ACRONYM_SPLIT = "$%%$";
    private static SentenceDetectorME sdetector = null;
    private static List<List<String>> acronymList = null;
    public static int id = 0;

    private Generator generator;

    public XMLParser() throws IOException {
        this.extension = "xml";
        this.generator = new Generator();
        if (sdetector == null) {
            sdetector = initSentDetector();
        }
        if (acronymList == null) {
            acronymList = initAcronymList();
        }
    }

    private static List<List<String>> initAcronymList() throws FileNotFoundException {
        List<List<String>> retList = new ArrayList<>();
        Scanner scanner = new Scanner(new File("configuration/acronyms.txt"));
        while (scanner.hasNextLine()) {
            String line = scanner.nextLine();
            String[] acrList = line.toLowerCase().split("\t");
            retList.add(Arrays.asList(acrList));
        }
        scanner.close();
        return retList;
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
        Document doc = getDocument(path); // get XML Document instance

        JSONObject articleInfo = getArticleInfo(doc);
        JSONObject[] tableList = getTableList(doc);
        JSONObject[] docList = null;
        JSONArray domains = (JSONArray) articleInfo.get("domains");
        boolean interested = false;
        for (int i = 0; i < domains.size(); i++) {
            if (((String) domains.get(i)).equals("Computer Science")) {
                interested = true;
                break;
            }
        }
        if (interested) {
            docList = new JSONObject[tableList.length];
            for (int i = 0; i < tableList.length; i++) {
                docList[i] = new JSONObject();
                tableList[i].putAll(articleInfo);
                if (tableList[i].containsKey("path")) {
                    docList[i].put("path", tableList[i].get("path"));
                } else {
                    tableList[i].put("path", path.toString());
                    docList[i].put("path", path.toString());
                }
                docList[i].put("source", tableList[i].toJSONString());
                docList[i].put("type", "table");
                docList[i].put("id", String.valueOf(id++));
            }
        }

        return docList;
    }

    private String getTextWithAcronym(Node node) {
        return expandAcronyms(node.getTextContent());
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
        // html
        NodeList nList = doc.getElementsByTagName("html");
        if (nList.getLength() != 0) {
            String html = nList.item(0).getTextContent();
            retTable.put("html", html);
        }
        // caption
        nList = doc.getElementsByTagName("caption");
        if (nList.getLength() != 0) {
            String caption = getTextWithAcronym(nList.item(0)).replaceAll("\\?\\?", "");
            retTable.put("caption", caption);
            retTable.put("short-caption", caption);
            String[] sentences = sdetector.sentDetect(caption);
            if (sentences.length > 1) {
                String shortCap = null;
                if (sentences[0].toLowerCase().startsWith("table") && sentences[0].length() < 10) {
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
        // acronyms
        nList = doc.getElementsByTagName("acronyms");
        if (nList.getLength() != 0) {
            String acronyms = nList.item(0).getTextContent();
            retTable.put("acronyms", acronyms);
        }
        // footnotes
        nList = doc.getElementsByTagName("footnote");
        if (nList.getLength() > 0) {
            JSONArray fnAry = new JSONArray();
            for (int i = 0; i < nList.getLength(); i++) {
                fnAry.add(getTextWithAcronym(nList.item(i)));
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
                        citeAry.add(getTextWithAcronym(node));
                    }
                } catch (XPathExpressionException e) {
                    e.printStackTrace();
                }
            }
            retTable.put("headings", headAry);
            retTable.put("citations", citeAry);
        }
        // headers and rows
        String headerField = getHeadersFromXml(doc, "headers", "header");
        retTable.put("col_header_field", headerField);
//        retTable.put("headers", getHeadersFromXml(doc, "headers", "header");
        Object[] rowObject = getDataRowsFromXml(doc);
        retTable.put("row_header_field", rowObject[0]);
        retTable.put("data", rowObject[1]);
        retTable.put("column_stats", getColumnStats(doc));
        return retTable;
    }

    private String getColumnStats(Element doc) {
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
        return columnStats.toJSONString();
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

    private Object[] getDataRowsFromXml(Element doc) {
        StringBuilder sb = new StringBuilder();
        JSONObject retRows = new JSONObject();
        NodeList nList = doc.getElementsByTagName("row");
        for (int i = 0; i < nList.getLength(); i++) {
            Element rowNode = (Element) nList.item(i);
            JSONObject dataRow = new JSONObject();
            JSONArray valueAry = new JSONArray();
            NodeList cellList = rowNode.getElementsByTagName("value");
            if (cellList.getLength() > 0) {
                // assume the first and only the first value of each data row is the row header
                String rowHeader = cellList.item(0).getTextContent();
                dataRow.put("row_header", rowHeader);
                sb.append(rowHeader);
                if (i != nList.getLength() - 1) {
                    sb.append(SPLIT);
                }

                for (int j = 1; j < cellList.getLength(); j++) {
                    String text = cellList.item(j).getTextContent();
                    text = replaceMinusSign(text);
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
        return new Object[]{expandAcronyms(sb.toString()), retRows.toJSONString()};
    }

    private String expandAcronyms(String text) {
        StringBuilder sb = new StringBuilder();
        String lowerText = text.toLowerCase();
        for (List<String> acrGroup : acronymList) {
            String full = acrGroup.get(0);
            if (lowerText.contains(full)) {
                sb.append(" ").append(String.join(" ", acrGroup.subList(1, acrGroup.size())));
                break;
            }
        }
        return String.join(" ", Arrays.asList(text, ACRONYM_SPLIT, sb.toString()));
//        return String.join(" ", Arrays.asList(text, ACRONYM_SPLIT, ""));
    }

    private String replaceMinusSign(String text) {
        String retStr = text;
        if (text.startsWith("−") || text.startsWith("–")) {
            retStr = "-" + text.substring(1);
        }
        return retStr;
    }

    private String getHeadersFromXml(Element doc, String rowTag, String cellTag) {
        StringBuilder sb = new StringBuilder();
        NodeList nList = doc.getElementsByTagName(rowTag);
        for (int i = 0; i < nList.getLength(); i++) {
            Element rowNode = (Element) nList.item(i);
            NodeList cellList = rowNode.getElementsByTagName(cellTag);
            for (int j = 0; j < cellList.getLength(); j++) {
                Node cell = cellList.item(j);
                String header = cell.getTextContent();
                sb.append(header);
                if (j != cellList.getLength() - 1) {
                    sb.append(SPLIT);
                }
            }
            if (i != nList.getLength() - 1) {
                sb.append(NEWLINE);
            }
        }
        return expandAcronyms(sb.toString());
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
        articleInfo.put("article-title", getTextWithAcronym(title));
        articleInfo.put("authors", listFromXml(doc, "author"));
        articleInfo.put("keywords", listFromXml(doc, "keyword"));
        NodeList abs = doc.getElementsByTagName("abstract");
        if (abs.getLength() != 0) {
            articleInfo.put("abstract", getTextWithAcronym(abs.item(0)));
        }
        NodeList link = doc.getElementsByTagName("link");
        if (link.getLength() != 0) {
            articleInfo.put("link", link.item(0).getTextContent());
        }

        // arXiv specific info
        String pathAsId = link.item(0).getTextContent().substring(21);
        articleInfo.put("path", pathAsId);
        Set<String> domainSet = new HashSet<String>();
        JSONArray subdomainAry = new JSONArray();
        NodeList domainList = doc.getElementsByTagName("domain");
        for (int i = 0; i < domainList.getLength(); i++) {
            Node domain = domainList.item(i);
            Element domainElm = (Element) domain;
            NodeList subList = domainElm.getElementsByTagName("subdomain");
            if (subList.getLength() != 0) {
                Node subdomain = subList.item(0);
                domain.removeChild(subdomain);
                subdomainAry.add(String.format("%s - %s",
                        domain.getTextContent().trim(), subdomain.getTextContent().trim()));
            }
            domainSet.add(domain.getTextContent().trim());
        }
        JSONArray domainAry = new JSONArray();
        for (String domain : domainSet) {
            domainAry.add(domain);
        }
        articleInfo.put("domains", domainAry);
        articleInfo.put("subdomains", subdomainAry);

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
