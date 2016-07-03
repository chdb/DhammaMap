(function (){ 'use strict';
/**
 * @ngdoc overview
 * @name dhammamapApp
 * @description
 * # dhammamapApp
 *
 * Main module of the application.
 */
angular
	.module('dhammamapApp'
			 , ['ngAnimate'
				,'ngAria'
				,'ngCookies'
				,'ngMessages'
				,'ngResource'
				//,'ngRoute'
				,'ngSanitize'
				,'ngTouch'					 
				,'ui.router'
				,'ui.sortable'
				,'LocalStorageModule'
	])
	.config(['localStorageServiceProvider'
			  , function (lssp){
					lssp.setPrefix('ls');
	}])
	// .config(['$routeProvider'
			  // , function (rp)
			  // { rp.when('/'
						  // ,{ templateUrl : 'views/main.html'
							// , controller  : 'MainCtrl'
							// , controllerAs: 'main'
						  // })
					// .when('/about'
						  // ,{ templateUrl : 'views/about.html'
							// , controller  : 'AboutCtrl'
							// , controllerAs: 'about'
						  // })
					// .when('/login'
						  // ,{ templateUrl : 'views/login.html'
							// , controller  : 'LoginCtrl'
							// , controllerAs: 'login'
						  // })
					// .otherwise
						  // ({ redirectTo: '/' });
	// }]);
// .config(['$stateProvider', '$urlRouterProvider', function ($stateProvider, $urlRouterProvider) //
	.config(['$stateProvider', function ($stateProvider) 
    { $stateProvider
			.state ('home' , { url:'/'
								  , templateUrl: 'views/main.html'
								  , controller: 'MainCtrl'
								  , controllerAs: 'main'
								  })
			.state ('about', { url:'/about'
								  , templateUrl: 'views/about.html'
								  , controller: 'AboutCtrl'
								  , controllerAs: 'about'
								  })
			.state ('login', { url:'/login'
								  , templateUrl: 'views/login.html'
								  , controller: 'LoginCtrl'
								  , controllerAs: 'login'
								  })
			.state ('contact', { url:'/contact'
								//  , templateUrl: 'views/contact.html'
								//  , controller: 'contactCtrl'
								//  , controllerAs: 'contact'
								  })
					  ;
	 }]);

				 
/*run.$inject = ['$rootScope', '$location', '$cookieStore', '$http'];
function run($rootScope, $location, $cookieStore, $http) {
	// keep user logged in after page refresh
	$rootScope.globals = $cookieStore.get('globals') || {};
	var loggedIn = $rootScope.globals.currentUser;
	if (loggedIn) {
		$http.defaults.headers.common['Authorization'] = 'Basic ' + loggedIn.authdata; // jshint ignore:line
	}

	$rootScope.$on('$locationChangeStart', function (event, next, current) {
		// redirect to login page if not logged in and trying to access a restricted page
		var restrictedPage = $.inArray($location.path(), ['/login', '/register']) === -1;
		loggedIn = $rootScope.globals.currentUser;
		if (restrictedPage && !loggedIn) {
			 $location.path('/login');
		}
	});
}*/
}());