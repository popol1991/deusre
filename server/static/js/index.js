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

/* Module */
window.Calaca = angular.module('calaca', ['elasticsearch'],
    ['$locationProvider', function($locationProvider){
        $locationProvider.html5Mode(true);
    }]
);

/* Controller
 *
 * On change in search box, search() will be called, and results are bind to scope as results[]
 *
*/
Calaca.controller('calacaCtrl', ['$scope', '$location', function($scope, $location){

        //Init empty array
        $scope.doctypelist = ["table", "row", "column"];
        $scope.type = $scope.doctypelist[0];

        $scope.home = function() {
            window.location="search.html";
        }

        $scope.search = function() {
            var url = "/yingkaig/eager/?q=" + $scope.query + "&type=" + $scope.type;
            window.location=url;
        };
    }]
);
