'use strict';
/* jshint laxcomma:true */

/**
 * @ngdoc function
 * @name dhammamapClientApp.controller:MainCtrl
 * @description
 * # MainCtrl
 * Controller of the dhammamapClientApp
 */
angular.module	('dhammamapClientApp')
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
	}]);

