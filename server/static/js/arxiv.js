var app = angular.module('filter', ['ngSanitize', 'ui.select']);

app.config(['$interpolateProvider', function($interpolateProvider) {
    $interpolateProvider.startSymbol('{[');
    $interpolateProvider.endSymbol(']}');
}]);

app.controller('filterCtrl', function($scope) {
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
        name: 'magnitude'
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
        label: 'Stddev',
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
        label: 'magnitude',
        name: 'mag'
    }
    ];

    $scope.filterlist = [
    ];

    $scope.addFilter = function() {
        $scope.filterlist.push({
            selected: $scope.filters[0]
        });
    }
});

app.filter('propsFilter', function() {
  return function(items, props) {
    var out = [];

    if (angular.isArray(items)) {
      items.forEach(function(item) {
        var itemMatches = false;

        var keys = Object.keys(props);
        for (var i = 0; i < keys.length; i++) {
          var prop = keys[i];
          var text = props[prop].toLowerCase();
          if (item[prop].toString().toLowerCase().indexOf(text) !== -1) {
            itemMatches = true;
            break;
          }
        }

        if (itemMatches) {
          out.push(item);
        }
      });
    } else {
      // Let the output be the input untouched
      out = items;
    }

    return out;
  };
});

app.controller('sideBar', function($scope, $http, $timeout) {
    $scope.subdomains = undefined;

    $scope.domainlist = [
        {
            id: 0,
            label: 'All Domains',
            value: 'all'
        },
        {
            id: 1,
            label: 'Physics',
            value: 'Physics'
        },
        {
            id: 2,
            label: 'Mathematics',
            value: 'Mathematics'
        },
        {
            id: 3,
            label: 'Computer Science',
            value: 'Computer Science'
        },
        {
            id: 4,
            label: 'Quantitative Biology',
            value: 'Quantitative Biology'
        },
        {
            id: 5,
            label: 'Quantitative Finance',
            value: 'Quantitative Finance'
        },
        {
            id: 6,
            label: 'Statistics',
            value: 'Statistics'
        }
    ];

    $scope.selected_domain = $scope.domainlist[0];

    $scope.update_subdomain = function() {
        $http.get('./subjects.json').
            success(function(data, status, headers, config) {
                $scope.subdomains = data[$scope.selected_domain.label];
        }).
            error(function(data, status, header, config) {
                alert("Subject loading failed.");
        });
    };

    $scope.counter = 0;
    $scope.someFunction = function (item, model){
        $scope.counter++;
        $scope.eventResult = {item: item, model: model};
    };

    $scope.multipleDemo = {};
    $scope.multipleDemo.colors = [];

});
