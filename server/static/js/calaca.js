/*
 * Calaca
 * Simple search client for ElasticSearch
 * https://github.com/romansanchez/Calaca
 * Author - Roman Sanchez
 * http://romansanchez.me
 * @rooomansanchez
 *
 * v1.0.1
 * MIT License
 */

/* Configs */
var indexName = "table";
var maxResultsSize = 20;
var host = "localhost";
var port = "9200";
var metalist = ['caption', 'issue', 'journal', 'issn', 'volume', 'page', 'date', 'article-title']
var global_info = ['caption', 'footnote_*', 'heading_*', 'citation_*']
var typeFields = {
    'table' : ["header_rows.header_*", "data_rows.svalue_0"].concat(global_info),
    'row' : ["header_rows.header_*", "data_rows.svalue_0"].concat(global_info),
    'column' : ["header_rows.header_*", "data_rows.svalue_0"].concat(global_info)
}

/* Module */
window.Calaca = angular.module('calaca', ['elasticsearch'],
    ['$locationProvider', function($locationProvider){
        $locationProvider.html5Mode(true);
    }]
);

/* Service to ES */
Calaca.factory('calacaService',
    ['$q', 'esFactory', '$location', function($q, elasticsearch, $location) {

         //Defaults if host and port aren't configured above
        var esHost = (host.length > 0 ) ? host : $location.host();
        var esPort = (port.length > 0 ) ? port : 9200;

        var client = elasticsearch({ host: esHost + ":" + esPort });

        var search = function(term, type, page) {

            var deferred = $q.defer();

            client.search({
                'index': indexName,
                'type': type,
                'size': maxResultsSize + 1,
                'from': page,
                'body': {
                    'query': {
                        'multi_match': {
                            'query' : term,
                            'type' : 'cross_fields',
                            'fields' : typeFields[type]
                        }
                    },
                    'highlight' : {
                        'fields' : {
                            'header_rows.header_*' : {},
                            'data_rows.svalue_0' : {},
                            'caption' : {},
                            'footnote_*' : {},
                            'heading_*' : {},
                            'citation_*' : {}
                        }
                    }
                }
            }).then(function(result) {
                //result = JSON.parse(result);
                var ii = 0, hits_in, hits_out = [];
                hits_in = (result.hits || {}).hits || [];
                for(;ii < hits_in.length; ii++){
                    hits_out.push(hits_in[ii]);
                }
                deferred.resolve(hits_out);
            }, deferred.reject);

            return deferred.promise;
        };

        var mlt = function(id, fields, type) {
            var deferred = $q.defer();
            client.search({
                'index' : indexName,
                'type' : type,
                'size' : 5,
                'body' : {
                    'query' : {
                        'more_like_this' : {
                            'fields' : fields,
                            'ids' : [id],
                            'min_term_freq' : 1,
                            'min_doc_freq' : 1,
                            'include' : false
                        }
                    }
                }
            }).then(function(result){
                //result = JSON.parse(result);
                var ii = 0, hits_in, hits_out = [];
                hits_in = (result.hits || {}).hits || [];
                for(;ii < hits_in.length; ii++){
                    hits_out.push(hits_in[ii]);
                }
                deferred.resolve(hits_out);
            }, deferred.reject);
            return deferred.promise;
        };

        return {
            "search": search,
            "mlt" : mlt
        };
    }]
);

Calaca.factory('aggregate', [function() {
    function comparer(a, b) {
        return a._source.table_id - b._source.table_id;
    };

    function group_row(results) {
        var ret = [];
        var prev_meta = results[0];
        var prev = prev_meta._source;
        var i = 1;
        while (i < results.length) {
            var cur_meta = results[i]
            var cur = cur_meta._source;
            if (cur['table_id'] == prev['table_id']) {
                prev['data_rows'].push(cur['data_rows'][0]);
            } else {
                ret.push(prev_meta);
                prev = cur;
                prev_meta = cur_meta
            }
            i++;
        }
        ret.push(prev_meta);
        return ret;
    };

    function group_column(results) {
        var ret = [];
        var prev_meta = results[0];
        var prev = prev_meta._source;
        var i = 1;
        while (i < results.length) {
            var cur_meta = results[i]
            var cur = cur_meta._source;
            if (cur['table_id'] == prev['table_id']) {
                for (var j = 0; j < cur['header_rows'].length; j++) {
                    for (var key in cur['header_rows'][j]) {
                        var info = key.split('_');
                        var idx = info[1];
                        if (idx == '1') {
                            var newKey = info[0] + '_' + cur['pos'];
                            prev['header_rows'][j][newKey] = cur['header_rows'][j][key];
                        }
                    }
                };
                for (var j = 0; j < cur['data_rows'].length; j++) {
                    for (var key in cur['data_rows'][j]) {
                        var info = key.split('_');
                        var idx = info[1];
                        if (idx == '1') {
                            var newKey = info[0] + '_' + cur['pos'];
                            prev['data_rows'][j][newKey] = cur['data_rows'][j][key];
                        }
                    }
                }
            } else {
                ret.push(prev_meta);
                prev = cur;
                prev_meta = cur_meta
            }
            i++;
        }
        ret.push(prev_meta);
        return ret;
    }

    var group = function(results, type) {
        // group data rows from the same table
        if (results.length == 0 || !('table_id' in results[0]._source)) {
            return results;
        }
        results.sort(comparer);
        if (type == 'row') {
            return group_row(results);
        } else if (type = 'column') {
            return group_column(results);
        }
    }

    return {
        'group' : group
    }
}]);

Calaca.factory('renderer', ['aggregate', function(aggregate) {
    function get_list(src, tag) {
        var retlist = [];
        for (var key in src) {
            if (key.search(tag) != -1) {
                idx = parseInt(key.split("_").slice(-1));
                retlist[idx] = src[key];
            }
        }
        return retlist;
    }

    function get_rows(src, tag) {
        var retlist = [];
        for (var i = 0; i < src.length; i++) {
            var row = get_list(src[i], tag);
            retlist.push(row);
        }
        return retlist;
    }

    var render = function(results, type) {
        var ret = [];
        var ii = 0;
        if (type != 'table') {
            results = aggregate.group(results, type);
        };
        for(;ii < results.length; ii++){
            var data = {};
            data._id = results[ii]._id;
            var table = results[ii]._source;
            for (var i = 0; i < metalist.length; i++) {
                var tag = metalist[i];
                if (tag in table) {
                    data[tag] = table[tag];
                }
            }
            data['authors'] = get_list(table, 'author');
            data['keywords'] = get_list(table, 'keyword');
            data['headings'] = get_list(table, 'heading');
            data['citations'] = get_list(table, 'citation');
            header_rows = get_rows(table['header_rows'], 'header');
            data_rows = get_rows(table['data_rows'], 'svalue');
            data["data_rows"] = data_rows;
            data["header_rows"] = header_rows;
            if ('highlight' in results[ii]) {
                matched_fields = [];
                for (var key in results[ii].highlight) {
                    matched_fields.push(key);
                }
                data['matched_fields'] = matched_fields;
            };
            ret.push(data);
        }
        return ret;
    };

    var panelStyle = function(style) {
        style.left = parseInt(window.innerWidth*0.05).toString() + "px";
        return style;
    };
    return {
        "render": render,
        "panelStyle" : panelStyle
    };
}]);

/* Controller
 *
 * On change in search box, search() will be called, and results are bind to scope as results[]
 *
*/
Calaca.controller('calacaCtrl', ['calacaService', 'renderer', '$scope', '$location', function(results, renderer, $scope, $location){

        //Init empty array
        $scope.results = [];
        $scope.mltresults = [];
        $scope.raw_results = [];
        $scope.doctypelist = ["table", "row", "column"];
        $scope.type = $scope.doctypelist[0];
        $scope.more = false;
        $scope.current_page = 0;
        $scope.hide = [];
        $scope.similarStyle = {};
        $scope.mltresult = true;

        //On search, reinitialize array, then perform search and load results
        $scope.search = function(more){
            if (more == 1) {
                $scope.current_page = $scope.current_page + 1;
            } else {
                $scope.current_page = 0;
            };
            $scope.results = [];
            $location.search({'q': $scope.query});
            $scope.loadResults($scope.current_page);
        };

        //Load search results into array
        $scope.loadResults = function(page) {
            results.search($scope.query, $scope.type, page)
            .then(function(results) {
                if (results.length > maxResultsSize) {
                    $scope.more = true;
                    results.pop();
                }
                $scope.raw_results = results;
                $scope.results = renderer.render(results, $scope.type);
                $scope.hide = [];
                for (i = 0; i < $scope.results.length; i++) {
                    $scope.hide.push(true);
                };
            });
        };

        $scope.home = function() {
            window.location="search.html";
        };

        $scope.toggle = function(id) {
            $scope.hide[id] = !$scope.hide[id];
        };

        $scope.mlt = function(id, type) {
            var matched_fields = Object.keys($scope.raw_results[id].highlight);
            results.mlt($scope.raw_results[id]._id, matched_fields, type)
            .then(function(results) {
                $scope.mltresults = renderer.render(results, $scope.type);
                $scope.similarStyle = renderer.panelStyle($scope.similarStyle);
                $scope.mltresult = false;
            });
        };

        $scope.closeSimilar = function() {
            if (!$scope.mltresult) {
                $scope.mltresult = true;
            }
        }

        $scope.is_type = function(type) {
            return type != $scope.type;
        };

        var init = function() {
            var query = $location.search()['q'];
            var type = $location.search()['type'];
            if (query != undefined) {
                $scope.query = query;
                $scope.type = type;
                $scope.search(0);
            }
        };
        init();
    }]
);
