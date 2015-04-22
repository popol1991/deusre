var app = angular.module('filter', []);

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
