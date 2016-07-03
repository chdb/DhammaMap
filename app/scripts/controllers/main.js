'use strict';
/* jshint laxcomma:true */

/**
 * @ngdoc function
 * @name dhammamapApp.controller:MainCtrl
 * @description
 * # MainCtrl
 * Controller of the dhammamapApp
 */
angular.module	('dhammamapApp')
	.controller ( 'MainCtrl'
					, ['$scope'
					  ,'localStorageService'
					  , function(s, lss) {
		var storedTodos = lss.get('todos');
		s.todos = storedTodos || [];
		s.$watch ('todos'
					, function () { lss.set('todos', s.todos);}
					, true
					);

		s.addTodo = function () {
			s.todos.push({'v': s.todo});
			s.todo = '';
		};

		s.removeTodo = function (index) {
			s.todos.splice(index, 1);
		};
	}])
	
/*	.controller('NavCtrl', function ($scope, $location) 
	{ 	// BS-NavBar does not set the selected tab's bg colour because BS does not set it to active, we have to do that ourselves.
		$scope.isActive = function (viewLocation) { 
			return viewLocation === $location.path();
		};
		// .. alternatively if using UI Router, then no controller needed instead just use the ui-sref-active/ui-sref-active-eq directives, 
		//ie. ui-sref-active-eq='active' or ui-sref-active='active' to achieve the same result.
		
		// NB there is another issue - the border of active tab is not shown in Chrome, although shown dotted in Firefox
	})
*/	;

