// /** @odoo-module **/
// // import ajax from "@web/legacy/js/core/ajax";
// // import { rpc } from "@web/core/network/rpc_service";
// import { rpc } from "@web/core/network/rpc";


// var vapid = ''
// var firebaseConfig = {};
// // ajax.rpc("/web/_config", 'call', {}).then(function (data) {
// rpc("/web/_config").then(function (data) {
//     console.log("\n\n\n\n\n\n\n Dataa", data);
//     if(data){

//     var json = JSON.parse(data)
//     vapid = json.vapid
//     firebaseConfig = json.config
//     firebase.initializeApp(firebaseConfig);
//     const messaging = firebase.messaging();

//     messaging.onMessage((payload) => {

//         const notificationOptions = {
//             body: payload.notification.body,
//         };
//         let notification = payload.notification;
//         navigator.serviceWorker.getRegistrations().then((registration) => {
//             registration[0].showNotification(notification.title, notificationOptions);
//         });
//     });
//     messaging.requestPermission()
//         .then(function () {
//             messaging.getToken({ vapidKey: vapid }).then((currentToken) => {
//                 if (currentToken) {                        
//                     $.post("/web/push_token",
//                         {
//                             name: currentToken
//                         })
//                 } else {
//                     console.log('No registration token available. Request permission to generate one.');
//                 }
//             }).catch((err) => {
//                 console.log('An error occurred while retrieving token. ', err);
//             });
//         })
        
//     }
// });