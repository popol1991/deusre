var app = angular.module('filter', []);

app.config(['$interpolateProvider', function($interpolateProvider) {
    $interpolateProvider.startSymbol('{[');
    $interpolateProvider.endSymbol(']}');
}]);

app.controller('facetCtrl', ['$scope', '$http', function($scope, $http) {
    $http.get('/deusre/judge/unit.json').success(function (data) {
        $scope.unitsMap = eval(data);
    });
}]);

app.controller('filterCtrl', ['$scope', '$location', function($scope, $location) {
    $scope.filters = [{
        id: 1,
        label: 'Value',
        name: 'mainValue'
    }, {
        id: 2,
        label: 'Error',
        name: 'precision'
    }, {
        id: 3,
        label: 'Magnitude',
        name: 'mag'
    }, {
        id: 4,
        label: 'p-value',
        name: 'pvalue'
    }, {
        id: 5,
        label: 'Integer Ratio',
        name: 'int_ratio'
    }, {
        id: 6,
        label: 'Real Ratio',
        name: 'float_ratio'
    }, {
        id: 7,
        label: 'Mean',
        name: 'mean'
    }, {
        id: 8,
        label: 'StdDev',
        name: 'std'
    }, {
        id: 9,
        label: 'Range',
        name: 'range'
    }, {
        id: 10,
        label: 'Accuracy',
        name: 'accuracy'
    }, {
        id: 11,
        label: 'Magnitude',
        name: 'mag'
    }
    ];

    $scope.filterlist = [
    ];

    $scope.addFilter = function() {
        $scope.filterlist.push({
            selected: $scope.filters[0]
        });
    };

    $scope.remove = function(index) {
        $scope.filterlist.splice(index, 1);
    };

    var parseLocation = function(location) {
        var pairs = location.substring(1).split("&");
        var obj = {};
        var pair;
        var i;

        for ( i in pairs ) {
          if ( pairs[i] === "" ) continue;

          pair = pairs[i].split("=");
          obj[ decodeURIComponent( pair[0] ) ] = decodeURIComponent( pair[1] );
        }

        return obj;
    };

    $scope.init = function() {
        var location = window.location.search;
        var params = parseLocation(location);
        var filterdict = {}
        for (var filter in params) {
            if (params.hasOwnProperty(filter)) {
                if (filter != "q") {
                    var info = filter.split("_");
                    name = info[0];
                    bound = info[1]
                    if ( !filterdict.hasOwnProperty(name) ) {
                        filterdict[name] = {};
                    }
                    filterdict[name][bound] = params[filter];
                }
            }
        }
        for (var i in $scope.filters) {
            var filter = jQuery.extend({}, $scope.filters[i]);
            if (filterdict.hasOwnProperty(filter.name)) {
                filter['min'] = filterdict[filter.name]['min'];
                filter['max'] = filterdict[filter.name]['max'];
                $scope.filterlist.push({
                    selected: filter
                })
            }
        }
    }

    $scope.init();
}]);

