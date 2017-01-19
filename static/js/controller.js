var ISSChatApp = angular.module('ISSChatApp', []);

ISSChatApp.controller('ChatController', function($scope){
   var socket = io.connect('https://' + document.domain + ':' 
   +location.port + '/iss'); 
    
    $scope.messages = [];
    $scope.name = '';
    $scope.text = '';
    

    socket.on('message', function(msg){
       console.log(msg);
       $scope.messages.push(msg);
       $scope.$apply();
       var elem = document.getElementById('msgpane');
       elem.scrollTop = elem.scrollHeight;
        
    });
    
    $scope.send = function send(){
        console.log('Sending message: ', $scope.text)
        socket.emit('message', $scope.text);
        $scope.text = '';
    }
    
    $scope.setName = function setName(){
       socket.emit('identify', $scope.name)  
    };
    
    socket.on('connect', function(){
        console.log('connected');
    });
    
});