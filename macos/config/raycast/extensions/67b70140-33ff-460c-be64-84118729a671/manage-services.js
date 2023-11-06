"use strict";var ln=Object.create;var M=Object.defineProperty;var dn=Object.getOwnPropertyDescriptor;var fn=Object.getOwnPropertyNames;var pn=Object.getPrototypeOf,mn=Object.prototype.hasOwnProperty;var p=(e,t)=>()=>(t||e((t={exports:{}}).exports,t),t.exports),hn=(e,t)=>{for(var n in t)M(e,n,{get:t[n],enumerable:!0})},Pe=(e,t,n,r)=>{if(t&&typeof t=="object"||typeof t=="function")for(let o of fn(t))!mn.call(e,o)&&o!==n&&M(e,o,{get:()=>t[o],enumerable:!(r=dn(t,o))||r.enumerable});return e};var b=(e,t,n)=>(n=e!=null?ln(pn(e)):{},Pe(t||!e||!e.__esModule?M(n,"default",{value:e,enumerable:!0}):n,e)),Sn=e=>Pe(M({},"__esModule",{value:!0}),e);var Ge=p((Fr,Ae)=>{Ae.exports=Ce;Ce.sync=yn;var Ie=require("fs");function gn(e,t){var n=t.pathExt!==void 0?t.pathExt:process.env.PATHEXT;if(!n||(n=n.split(";"),n.indexOf("")!==-1))return!0;for(var r=0;r<n.length;r++){var o=n[r].toLowerCase();if(o&&e.substr(-o.length).toLowerCase()===o)return!0}return!1}function Te(e,t,n){return!e.isSymbolicLink()&&!e.isFile()?!1:gn(t,n)}function Ce(e,t,n){Ie.stat(e,function(r,o){n(r,r?!1:Te(o,e,t))})}function yn(e,t){return Te(Ie.statSync(e),e,t)}});var ke=p((Lr,Ne)=>{Ne.exports=$e;$e.sync=xn;var Re=require("fs");function $e(e,t,n){Re.stat(e,function(r,o){n(r,r?!1:Oe(o,t))})}function xn(e,t){return Oe(Re.statSync(e),t)}function Oe(e,t){return e.isFile()&&wn(e,t)}function wn(e,t){var n=e.mode,r=e.uid,o=e.gid,i=t.uid!==void 0?t.uid:process.getuid&&process.getuid(),s=t.gid!==void 0?t.gid:process.getgid&&process.getgid(),c=parseInt("100",8),l=parseInt("010",8),d=parseInt("001",8),f=c|l,g=n&d||n&l&&o===s||n&c&&r===i||n&f&&i===0;return g}});var Le=p((jr,Fe)=>{var Br=require("fs"),_;process.platform==="win32"||global.TESTING_WINDOWS?_=Ge():_=ke();Fe.exports=Y;Y.sync=bn;function Y(e,t,n){if(typeof t=="function"&&(n=t,t={}),!n){if(typeof Promise!="function")throw new TypeError("callback not provided");return new Promise(function(r,o){Y(e,t||{},function(i,s){i?o(i):r(s)})})}_(e,t||{},function(r,o){r&&(r.code==="EACCES"||t&&t.ignoreErrors)&&(r=null,o=!1),n(r,o)})}function bn(e,t){try{return _.sync(e,t||{})}catch(n){if(t&&t.ignoreErrors||n.code==="EACCES")return!1;throw n}}});var De=p((Mr,Ue)=>{var I=process.platform==="win32"||process.env.OSTYPE==="cygwin"||process.env.OSTYPE==="msys",Be=require("path"),vn=I?";":":",je=Le(),Me=e=>Object.assign(new Error(`not found: ${e}`),{code:"ENOENT"}),_e=(e,t)=>{let n=t.colon||vn,r=e.match(/\//)||I&&e.match(/\\/)?[""]:[...I?[process.cwd()]:[],...(t.path||process.env.PATH||"").split(n)],o=I?t.pathExt||process.env.PATHEXT||".EXE;.CMD;.BAT;.COM":"",i=I?o.split(n):[""];return I&&e.indexOf(".")!==-1&&i[0]!==""&&i.unshift(""),{pathEnv:r,pathExt:i,pathExtExe:o}},qe=(e,t,n)=>{typeof t=="function"&&(n=t,t={}),t||(t={});let{pathEnv:r,pathExt:o,pathExtExe:i}=_e(e,t),s=[],c=d=>new Promise((f,g)=>{if(d===r.length)return t.all&&s.length?f(s):g(Me(e));let S=r[d],y=/^".*"$/.test(S)?S.slice(1,-1):S,x=Be.join(y,e),w=!y&&/^\.[\\\/]/.test(e)?e.slice(0,2)+x:x;f(l(w,d,0))}),l=(d,f,g)=>new Promise((S,y)=>{if(g===o.length)return S(c(f+1));let x=o[g];je(d+x,{pathExt:i},(w,P)=>{if(!w&&P)if(t.all)s.push(d+x);else return S(d+x);return S(l(d,f,g+1))})});return n?c(0).then(d=>n(null,d),n):c(0)},En=(e,t)=>{t=t||{};let{pathEnv:n,pathExt:r,pathExtExe:o}=_e(e,t),i=[];for(let s=0;s<n.length;s++){let c=n[s],l=/^".*"$/.test(c)?c.slice(1,-1):c,d=Be.join(l,e),f=!l&&/^\.[\\\/]/.test(e)?e.slice(0,2)+d:d;for(let g=0;g<r.length;g++){let S=f+r[g];try{if(je.sync(S,{pathExt:o}))if(t.all)i.push(S);else return S}catch{}}}if(t.all&&i.length)return i;if(t.nothrow)return null;throw Me(e)};Ue.exports=qe;qe.sync=En});var Xe=p((_r,Q)=>{"use strict";var He=(e={})=>{let t=e.env||process.env;return(e.platform||process.platform)!=="win32"?"PATH":Object.keys(t).reverse().find(r=>r.toUpperCase()==="PATH")||"Path"};Q.exports=He;Q.exports.default=He});var Ve=p((qr,ze)=>{"use strict";var Ke=require("path"),Pn=De(),In=Xe();function We(e,t){let n=e.options.env||process.env,r=process.cwd(),o=e.options.cwd!=null,i=o&&process.chdir!==void 0&&!process.chdir.disabled;if(i)try{process.chdir(e.options.cwd)}catch{}let s;try{s=Pn.sync(e.command,{path:n[In({env:n})],pathExt:t?Ke.delimiter:void 0})}catch{}finally{i&&process.chdir(r)}return s&&(s=Ke.resolve(o?e.options.cwd:"",s)),s}function Tn(e){return We(e)||We(e,!0)}ze.exports=Tn});var Ye=p((Ur,J)=>{"use strict";var Z=/([()\][%!^"`<>&|;, *?])/g;function Cn(e){return e=e.replace(Z,"^$1"),e}function An(e,t){return e=`${e}`,e=e.replace(/(\\*)"/g,'$1$1\\"'),e=e.replace(/(\\*)$/,"$1$1"),e=`"${e}"`,e=e.replace(Z,"^$1"),t&&(e=e.replace(Z,"^$1")),e}J.exports.command=Cn;J.exports.argument=An});var Ze=p((Dr,Qe)=>{"use strict";Qe.exports=/^#!(.*)/});var et=p((Hr,Je)=>{"use strict";var Gn=Ze();Je.exports=(e="")=>{let t=e.match(Gn);if(!t)return null;let[n,r]=t[0].replace(/#! ?/,"").split(" "),o=n.split("/").pop();return o==="env"?r:r?`${o} ${r}`:o}});var nt=p((Xr,tt)=>{"use strict";var ee=require("fs"),Rn=et();function $n(e){let n=Buffer.alloc(150),r;try{r=ee.openSync(e,"r"),ee.readSync(r,n,0,150,0),ee.closeSync(r)}catch{}return Rn(n.toString())}tt.exports=$n});var st=p((Kr,it)=>{"use strict";var On=require("path"),rt=Ve(),ot=Ye(),Nn=nt(),kn=process.platform==="win32",Fn=/\.(?:com|exe)$/i,Ln=/node_modules[\\/].bin[\\/][^\\/]+\.cmd$/i;function Bn(e){e.file=rt(e);let t=e.file&&Nn(e.file);return t?(e.args.unshift(e.file),e.command=t,rt(e)):e.file}function jn(e){if(!kn)return e;let t=Bn(e),n=!Fn.test(t);if(e.options.forceShell||n){let r=Ln.test(t);e.command=On.normalize(e.command),e.command=ot.command(e.command),e.args=e.args.map(i=>ot.argument(i,r));let o=[e.command].concat(e.args).join(" ");e.args=["/d","/s","/c",`"${o}"`],e.command=process.env.comspec||"cmd.exe",e.options.windowsVerbatimArguments=!0}return e}function Mn(e,t,n){t&&!Array.isArray(t)&&(n=t,t=null),t=t?t.slice(0):[],n=Object.assign({},n);let r={command:e,args:t,options:n,file:void 0,original:{command:e,args:t}};return n.shell?r:jn(r)}it.exports=Mn});var ut=p((Wr,ct)=>{"use strict";var te=process.platform==="win32";function ne(e,t){return Object.assign(new Error(`${t} ${e.command} ENOENT`),{code:"ENOENT",errno:"ENOENT",syscall:`${t} ${e.command}`,path:e.command,spawnargs:e.args})}function _n(e,t){if(!te)return;let n=e.emit;e.emit=function(r,o){if(r==="exit"){let i=at(o,t,"spawn");if(i)return n.call(e,"error",i)}return n.apply(e,arguments)}}function at(e,t){return te&&e===1&&!t.file?ne(t.original,"spawn"):null}function qn(e,t){return te&&e===1&&!t.file?ne(t.original,"spawnSync"):null}ct.exports={hookChildProcess:_n,verifyENOENT:at,verifyENOENTSync:qn,notFoundError:ne}});var ft=p((zr,T)=>{"use strict";var lt=require("child_process"),re=st(),oe=ut();function dt(e,t,n){let r=re(e,t,n),o=lt.spawn(r.command,r.args,r.options);return oe.hookChildProcess(o,r),o}function Un(e,t,n){let r=re(e,t,n),o=lt.spawnSync(r.command,r.args,r.options);return o.error=o.error||oe.verifyENOENTSync(o.status,r),o}T.exports=dt;T.exports.spawn=dt;T.exports.sync=Un;T.exports._parse=re;T.exports._enoent=oe});var Et=p((ho,H)=>{H.exports=["SIGABRT","SIGALRM","SIGHUP","SIGINT","SIGTERM"];process.platform!=="win32"&&H.exports.push("SIGVTALRM","SIGXCPU","SIGXFSZ","SIGUSR2","SIGTRAP","SIGSYS","SIGQUIT","SIGIOT");process.platform==="linux"&&H.exports.push("SIGIO","SIGPOLL","SIGPWR","SIGSTKFLT","SIGUNUSED")});var At=p((So,R)=>{var u=global.process;typeof u!="object"||!u?R.exports=function(){}:(Pt=require("assert"),A=Et(),It=/^win/i.test(u.platform),N=require("events"),typeof N!="function"&&(N=N.EventEmitter),u.__signal_exit_emitter__?m=u.__signal_exit_emitter__:(m=u.__signal_exit_emitter__=new N,m.count=0,m.emitted={}),m.infinite||(m.setMaxListeners(1/0),m.infinite=!0),R.exports=function(e,t){if(global.process===u){Pt.equal(typeof e,"function","a callback must be provided for exit handler"),G===!1&&le();var n="exit";t&&t.alwaysLast&&(n="afterexit");var r=function(){m.removeListener(n,e),m.listeners("exit").length===0&&m.listeners("afterexit").length===0&&X()};return m.on(n,e),r}},X=function(){!G||global.process!==u||(G=!1,A.forEach(function(t){try{u.removeListener(t,K[t])}catch{}}),u.emit=W,u.reallyExit=de,m.count-=1)},R.exports.unload=X,v=function(t,n,r){m.emitted[t]||(m.emitted[t]=!0,m.emit(t,n,r))},K={},A.forEach(function(e){K[e]=function(){if(u===global.process){var n=u.listeners(e);n.length===m.count&&(X(),v("exit",null,e),v("afterexit",null,e),It&&e==="SIGHUP"&&(e="SIGINT"),u.kill(u.pid,e))}}}),R.exports.signals=function(){return A},G=!1,le=function(){G||u!==global.process||(G=!0,m.count+=1,A=A.filter(function(t){try{return u.on(t,K[t]),!0}catch{return!1}}),u.emit=Ct,u.reallyExit=Tt)},R.exports.load=le,de=u.reallyExit,Tt=function(t){u===global.process&&(u.exitCode=t||0,v("exit",u.exitCode,null),v("afterexit",u.exitCode,null),de.call(u,u.exitCode))},W=u.emit,Ct=function(t,n){if(t==="exit"&&u===global.process){n!==void 0&&(u.exitCode=n);var r=W.apply(this,arguments);return v("exit",u.exitCode,null),v("afterexit",u.exitCode,null),r}else return W.apply(this,arguments)});var Pt,A,It,N,m,X,v,K,G,le,de,Tt,W,Ct});var jt=p((xo,Bt)=>{"use strict";var{PassThrough:fr}=require("stream");Bt.exports=e=>{e={...e};let{array:t}=e,{encoding:n}=e,r=n==="buffer",o=!1;t?o=!(n||r):n=n||"utf8",r&&(n=null);let i=new fr({objectMode:o});n&&i.setEncoding(n);let s=0,c=[];return i.on("data",l=>{c.push(l),o?s=c.length:s+=l.length}),i.getBufferedValue=()=>t?c:r?Buffer.concat(c,s):c.join(""),i.getBufferedLength=()=>s,i}});var Mt=p((wo,k)=>{"use strict";var{constants:pr}=require("buffer"),mr=require("stream"),{promisify:hr}=require("util"),Sr=jt(),gr=hr(mr.pipeline),z=class extends Error{constructor(){super("maxBuffer exceeded"),this.name="MaxBufferError"}};async function fe(e,t){if(!e)throw new Error("Expected a stream");t={maxBuffer:1/0,...t};let{maxBuffer:n}=t,r=Sr(t);return await new Promise((o,i)=>{let s=c=>{c&&r.getBufferedLength()<=pr.MAX_LENGTH&&(c.bufferedData=r.getBufferedValue()),i(c)};(async()=>{try{await gr(e,r),o()}catch(c){s(c)}})(),r.on("data",()=>{r.getBufferedLength()>n&&s(new z)})}),r.getBufferedValue()}k.exports=fe;k.exports.buffer=(e,t)=>fe(e,{...t,encoding:"buffer"});k.exports.array=(e,t)=>fe(e,{...t,array:!0});k.exports.MaxBufferError=z});var qt=p((bo,_t)=>{"use strict";var{PassThrough:yr}=require("stream");_t.exports=function(){var e=[],t=new yr({objectMode:!0});return t.setMaxListeners(0),t.add=n,t.isEmpty=r,t.on("unpipe",o),Array.prototype.slice.call(arguments).forEach(n),t;function n(i){return Array.isArray(i)?(i.forEach(n),this):(e.push(i),i.once("end",o.bind(null,i)),i.once("error",t.emit.bind(t,"error")),i.pipe(t,{end:!1}),this)}function r(){return e.length==0}function o(i){e=e.filter(function(s){return s!==i}),!e.length&&t.readable&&t.end()}}});var Nr={};hn(Nr,{default:()=>an});module.exports=Sn(Nr);var V=require("react");var a=require("@raycast/api");var Qt=require("node:buffer"),Zt=b(require("node:path"),1),ye=b(require("node:child_process"),1),F=b(require("node:process"),1),Jt=b(ft(),1);function ie(e){let t=typeof e=="string"?`
`:`
`.charCodeAt(),n=typeof e=="string"?"\r":"\r".charCodeAt();return e[e.length-1]===t&&(e=e.slice(0,-1)),e[e.length-1]===n&&(e=e.slice(0,-1)),e}var O=b(require("node:process"),1),C=b(require("node:path"),1);function q(e={}){let{env:t=process.env,platform:n=process.platform}=e;return n!=="win32"?"PATH":Object.keys(t).reverse().find(r=>r.toUpperCase()==="PATH")||"Path"}function Dn(e={}){let{cwd:t=O.default.cwd(),path:n=O.default.env[q()],execPath:r=O.default.execPath}=e,o,i=C.default.resolve(t),s=[];for(;o!==i;)s.push(C.default.join(i,"node_modules/.bin")),o=i,i=C.default.resolve(i,"..");return s.push(C.default.resolve(t,r,"..")),[...s,n].join(C.default.delimiter)}function pt({env:e=O.default.env,...t}={}){e={...e};let n=q({env:e});return t.path=e[n],e[n]=Dn(t),e}var Hn=(e,t,n,r)=>{if(n==="length"||n==="prototype"||n==="arguments"||n==="caller")return;let o=Object.getOwnPropertyDescriptor(e,n),i=Object.getOwnPropertyDescriptor(t,n);!Xn(o,i)&&r||Object.defineProperty(e,n,i)},Xn=function(e,t){return e===void 0||e.configurable||e.writable===t.writable&&e.enumerable===t.enumerable&&e.configurable===t.configurable&&(e.writable||e.value===t.value)},Kn=(e,t)=>{let n=Object.getPrototypeOf(t);n!==Object.getPrototypeOf(e)&&Object.setPrototypeOf(e,n)},Wn=(e,t)=>`/* Wrapped ${e}*/
${t}`,zn=Object.getOwnPropertyDescriptor(Function.prototype,"toString"),Vn=Object.getOwnPropertyDescriptor(Function.prototype.toString,"name"),Yn=(e,t,n)=>{let r=n===""?"":`with ${n.trim()}() `,o=Wn.bind(null,r,t.toString());Object.defineProperty(o,"name",Vn),Object.defineProperty(e,"toString",{...zn,value:o})};function se(e,t,{ignoreNonConfigurable:n=!1}={}){let{name:r}=e;for(let o of Reflect.ownKeys(t))Hn(e,t,o,n);return Kn(e,t),Yn(e,t,r),e}var U=new WeakMap,mt=(e,t={})=>{if(typeof e!="function")throw new TypeError("Expected a function");let n,r=0,o=e.displayName||e.name||"<anonymous>",i=function(...s){if(U.set(i,++r),r===1)n=e.apply(this,s),e=null;else if(t.throw===!0)throw new Error(`Function \`${o}\` can only be called once`);return n};return se(i,e),U.set(i,r),i};mt.callCount=e=>{if(!U.has(e))throw new Error(`The given function \`${e.name}\` is not wrapped by the \`onetime\` package`);return U.get(e)};var ht=mt;var wt=require("os");var St=function(){let e=ae-gt+1;return Array.from({length:e},Qn)},Qn=function(e,t){return{name:`SIGRT${t+1}`,number:gt+t,action:"terminate",description:"Application-specific signal (realtime)",standard:"posix"}},gt=34,ae=64;var xt=require("os");var yt=[{name:"SIGHUP",number:1,action:"terminate",description:"Terminal closed",standard:"posix"},{name:"SIGINT",number:2,action:"terminate",description:"User interruption with CTRL-C",standard:"ansi"},{name:"SIGQUIT",number:3,action:"core",description:"User interruption with CTRL-\\",standard:"posix"},{name:"SIGILL",number:4,action:"core",description:"Invalid machine instruction",standard:"ansi"},{name:"SIGTRAP",number:5,action:"core",description:"Debugger breakpoint",standard:"posix"},{name:"SIGABRT",number:6,action:"core",description:"Aborted",standard:"ansi"},{name:"SIGIOT",number:6,action:"core",description:"Aborted",standard:"bsd"},{name:"SIGBUS",number:7,action:"core",description:"Bus error due to misaligned, non-existing address or paging error",standard:"bsd"},{name:"SIGEMT",number:7,action:"terminate",description:"Command should be emulated but is not implemented",standard:"other"},{name:"SIGFPE",number:8,action:"core",description:"Floating point arithmetic error",standard:"ansi"},{name:"SIGKILL",number:9,action:"terminate",description:"Forced termination",standard:"posix",forced:!0},{name:"SIGUSR1",number:10,action:"terminate",description:"Application-specific signal",standard:"posix"},{name:"SIGSEGV",number:11,action:"core",description:"Segmentation fault",standard:"ansi"},{name:"SIGUSR2",number:12,action:"terminate",description:"Application-specific signal",standard:"posix"},{name:"SIGPIPE",number:13,action:"terminate",description:"Broken pipe or socket",standard:"posix"},{name:"SIGALRM",number:14,action:"terminate",description:"Timeout or timer",standard:"posix"},{name:"SIGTERM",number:15,action:"terminate",description:"Termination",standard:"ansi"},{name:"SIGSTKFLT",number:16,action:"terminate",description:"Stack is empty or overflowed",standard:"other"},{name:"SIGCHLD",number:17,action:"ignore",description:"Child process terminated, paused or unpaused",standard:"posix"},{name:"SIGCLD",number:17,action:"ignore",description:"Child process terminated, paused or unpaused",standard:"other"},{name:"SIGCONT",number:18,action:"unpause",description:"Unpaused",standard:"posix",forced:!0},{name:"SIGSTOP",number:19,action:"pause",description:"Paused",standard:"posix",forced:!0},{name:"SIGTSTP",number:20,action:"pause",description:'Paused using CTRL-Z or "suspend"',standard:"posix"},{name:"SIGTTIN",number:21,action:"pause",description:"Background process cannot read terminal input",standard:"posix"},{name:"SIGBREAK",number:21,action:"terminate",description:"User interruption with CTRL-BREAK",standard:"other"},{name:"SIGTTOU",number:22,action:"pause",description:"Background process cannot write to terminal output",standard:"posix"},{name:"SIGURG",number:23,action:"ignore",description:"Socket received out-of-band data",standard:"bsd"},{name:"SIGXCPU",number:24,action:"core",description:"Process timed out",standard:"bsd"},{name:"SIGXFSZ",number:25,action:"core",description:"File too big",standard:"bsd"},{name:"SIGVTALRM",number:26,action:"terminate",description:"Timeout or timer",standard:"bsd"},{name:"SIGPROF",number:27,action:"terminate",description:"Timeout or timer",standard:"bsd"},{name:"SIGWINCH",number:28,action:"ignore",description:"Terminal window size changed",standard:"bsd"},{name:"SIGIO",number:29,action:"terminate",description:"I/O is available",standard:"other"},{name:"SIGPOLL",number:29,action:"terminate",description:"Watched event",standard:"other"},{name:"SIGINFO",number:29,action:"ignore",description:"Request for process information",standard:"other"},{name:"SIGPWR",number:30,action:"terminate",description:"Device running out of power",standard:"systemv"},{name:"SIGSYS",number:31,action:"core",description:"Invalid system call",standard:"other"},{name:"SIGUNUSED",number:31,action:"terminate",description:"Invalid system call",standard:"other"}];var ce=function(){let e=St();return[...yt,...e].map(Zn)},Zn=function({name:e,number:t,description:n,action:r,forced:o=!1,standard:i}){let{signals:{[e]:s}}=xt.constants,c=s!==void 0;return{name:e,number:c?s:t,description:n,supported:c,action:r,forced:o,standard:i}};var Jn=function(){return ce().reduce(er,{})},er=function(e,{name:t,number:n,description:r,supported:o,action:i,forced:s,standard:c}){return{...e,[t]:{name:t,number:n,description:r,supported:o,action:i,forced:s,standard:c}}},bt=Jn(),tr=function(){let e=ce(),t=64+1,n=Array.from({length:t},(r,o)=>nr(o,e));return Object.assign({},...n)},nr=function(e,t){let n=rr(e,t);if(n===void 0)return{};let{name:r,description:o,supported:i,action:s,forced:c,standard:l}=n;return{[e]:{name:r,number:e,description:o,supported:i,action:s,forced:c,standard:l}}},rr=function(e,t){let n=t.find(({name:r})=>wt.constants.signals[r]===e);return n!==void 0?n:t.find(r=>r.number===e)},uo=tr();var or=({timedOut:e,timeout:t,errorCode:n,signal:r,signalDescription:o,exitCode:i,isCanceled:s})=>e?`timed out after ${t} milliseconds`:s?"was canceled":n!==void 0?`failed with ${n}`:r!==void 0?`was killed with ${r} (${o})`:i!==void 0?`failed with exit code ${i}`:"failed",ue=({stdout:e,stderr:t,all:n,error:r,signal:o,exitCode:i,command:s,escapedCommand:c,timedOut:l,isCanceled:d,killed:f,parsed:{options:{timeout:g}}})=>{i=i===null?void 0:i,o=o===null?void 0:o;let S=o===void 0?void 0:bt[o].description,y=r&&r.code,w=`Command ${or({timedOut:l,timeout:g,errorCode:y,signal:o,signalDescription:S,exitCode:i,isCanceled:d})}: ${s}`,P=Object.prototype.toString.call(r)==="[object Error]",B=P?`${w}
${r.message}`:w,j=[B,t,e].filter(Boolean).join(`
`);return P?(r.originalMessage=r.message,r.message=j):r=new Error(j),r.shortMessage=B,r.command=s,r.escapedCommand=c,r.exitCode=i,r.signal=o,r.signalDescription=S,r.stdout=e,r.stderr=t,n!==void 0&&(r.all=n),"bufferedData"in r&&delete r.bufferedData,r.failed=!0,r.timedOut=!!l,r.isCanceled=d,r.killed=f&&!l,r};var D=["stdin","stdout","stderr"],ir=e=>D.some(t=>e[t]!==void 0),vt=e=>{if(!e)return;let{stdio:t}=e;if(t===void 0)return D.map(r=>e[r]);if(ir(e))throw new Error(`It's not possible to provide \`stdio\` in combination with one of ${D.map(r=>`\`${r}\``).join(", ")}`);if(typeof t=="string")return t;if(!Array.isArray(t))throw new TypeError(`Expected \`stdio\` to be of type \`string\` or \`Array\`, got \`${typeof t}\``);let n=Math.max(t.length,D.length);return Array.from({length:n},(r,o)=>t[o])};var Gt=b(require("node:os"),1),Rt=b(At(),1),sr=1e3*5,$t=(e,t="SIGTERM",n={})=>{let r=e(t);return ar(e,t,n,r),r},ar=(e,t,n,r)=>{if(!cr(t,n,r))return;let o=lr(n),i=setTimeout(()=>{e("SIGKILL")},o);i.unref&&i.unref()},cr=(e,{forceKillAfterTimeout:t},n)=>ur(e)&&t!==!1&&n,ur=e=>e===Gt.default.constants.signals.SIGTERM||typeof e=="string"&&e.toUpperCase()==="SIGTERM",lr=({forceKillAfterTimeout:e=!0})=>{if(e===!0)return sr;if(!Number.isFinite(e)||e<0)throw new TypeError(`Expected the \`forceKillAfterTimeout\` option to be a non-negative integer, got \`${e}\` (${typeof e})`);return e},Ot=(e,t)=>{e.kill()&&(t.isCanceled=!0)},dr=(e,t,n)=>{e.kill(t),n(Object.assign(new Error("Timed out"),{timedOut:!0,signal:t}))},Nt=(e,{timeout:t,killSignal:n="SIGTERM"},r)=>{if(t===0||t===void 0)return r;let o,i=new Promise((c,l)=>{o=setTimeout(()=>{dr(e,n,l)},t)}),s=r.finally(()=>{clearTimeout(o)});return Promise.race([i,s])},kt=({timeout:e})=>{if(e!==void 0&&(!Number.isFinite(e)||e<0))throw new TypeError(`Expected the \`timeout\` option to be a non-negative integer, got \`${e}\` (${typeof e})`)},Ft=async(e,{cleanup:t,detached:n},r)=>{if(!t||n)return r;let o=(0,Rt.default)(()=>{e.kill()});return r.finally(()=>{o()})};function Lt(e){return e!==null&&typeof e=="object"&&typeof e.pipe=="function"}var he=b(Mt(),1),Ut=b(qt(),1),Dt=(e,t)=>{t===void 0||e.stdin===void 0||(Lt(t)?t.pipe(e.stdin):e.stdin.end(t))},Ht=(e,{all:t})=>{if(!t||!e.stdout&&!e.stderr)return;let n=(0,Ut.default)();return e.stdout&&n.add(e.stdout),e.stderr&&n.add(e.stderr),n},pe=async(e,t)=>{if(e){e.destroy();try{return await t}catch(n){return n.bufferedData}}},me=(e,{encoding:t,buffer:n,maxBuffer:r})=>{if(!(!e||!n))return t?(0,he.default)(e,{encoding:t,maxBuffer:r}):he.default.buffer(e,{maxBuffer:r})},Xt=async({stdout:e,stderr:t,all:n},{encoding:r,buffer:o,maxBuffer:i},s)=>{let c=me(e,{encoding:r,buffer:o,maxBuffer:i}),l=me(t,{encoding:r,buffer:o,maxBuffer:i}),d=me(n,{encoding:r,buffer:o,maxBuffer:i*2});try{return await Promise.all([s,c,l,d])}catch(f){return Promise.all([{error:f,signal:f.signal,timedOut:f.timedOut},pe(e,c),pe(t,l),pe(n,d)])}};var xr=(async()=>{})().constructor.prototype,wr=["then","catch","finally"].map(e=>[e,Reflect.getOwnPropertyDescriptor(xr,e)]),Se=(e,t)=>{for(let[n,r]of wr){let o=typeof t=="function"?(...i)=>Reflect.apply(r.value,t(),i):r.value.bind(t);Reflect.defineProperty(e,n,{...r,value:o})}return e},Kt=e=>new Promise((t,n)=>{e.on("exit",(r,o)=>{t({exitCode:r,signal:o})}),e.on("error",r=>{n(r)}),e.stdin&&e.stdin.on("error",r=>{n(r)})});var Wt=(e,t=[])=>Array.isArray(t)?[e,...t]:[e],br=/^[\w.-]+$/,vr=/"/g,Er=e=>typeof e!="string"||br.test(e)?e:`"${e.replace(vr,'\\"')}"`,zt=(e,t)=>Wt(e,t).join(" "),Vt=(e,t)=>Wt(e,t).map(n=>Er(n)).join(" "),Pr=/ +/g,Yt=e=>{let t=[];for(let n of e.trim().split(Pr)){let r=t[t.length-1];r&&r.endsWith("\\")?t[t.length-1]=`${r.slice(0,-1)} ${n}`:t.push(n)}return t};var Ir=1e3*1e3*100,Tr=({env:e,extendEnv:t,preferLocal:n,localDir:r,execPath:o})=>{let i=t?{...F.default.env,...e}:e;return n?pt({env:i,cwd:r,execPath:o}):i},Cr=(e,t,n={})=>{let r=Jt.default._parse(e,t,n);return e=r.command,t=r.args,n=r.options,n={maxBuffer:Ir,buffer:!0,stripFinalNewline:!0,extendEnv:!0,preferLocal:!1,localDir:n.cwd||F.default.cwd(),execPath:F.default.execPath,encoding:"utf8",reject:!0,cleanup:!0,all:!1,windowsHide:!0,...n},n.env=Tr(n),n.stdio=vt(n),F.default.platform==="win32"&&Zt.default.basename(e,".exe")==="cmd"&&t.unshift("/q"),{file:e,args:t,options:n,parsed:r}},ge=(e,t,n)=>typeof t!="string"&&!Qt.Buffer.isBuffer(t)?n===void 0?void 0:"":e.stripFinalNewline?ie(t):t;function Ar(e,t,n){let r=Cr(e,t,n),o=zt(e,t),i=Vt(e,t);kt(r.options);let s;try{s=ye.default.spawn(r.file,r.args,r.options)}catch(y){let x=new ye.default.ChildProcess,w=Promise.reject(ue({error:y,stdout:"",stderr:"",all:"",command:o,escapedCommand:i,parsed:r,timedOut:!1,isCanceled:!1,killed:!1}));return Se(x,w)}let c=Kt(s),l=Nt(s,r.options,c),d=Ft(s,r.options,l),f={isCanceled:!1};s.kill=$t.bind(null,s.kill.bind(s)),s.cancel=Ot.bind(null,s,f);let S=ht(async()=>{let[{error:y,exitCode:x,signal:w,timedOut:P},B,j,un]=await Xt(s,r.options,d),we=ge(r.options,B),be=ge(r.options,j),ve=ge(r.options,un);if(y||x!==0||w!==null){let Ee=ue({error:y,exitCode:x,signal:w,stdout:we,stderr:be,all:ve,command:o,escapedCommand:i,parsed:r,timedOut:P,isCanceled:f.isCanceled,killed:s.killed});if(!r.options.reject)return Ee;throw Ee}return{command:o,escapedCommand:i,exitCode:0,stdout:we,stderr:be,all:ve,failed:!1,timedOut:!1,isCanceled:!1,killed:!1}});return Dt(s,r.options.input),s.all=Ht(s,r.options),Se(s,S)}function en(e,t){let[n,...r]=Yt(e);return Ar(n,r,t)}var rn=require("fs"),on=require("os"),h=require("react/jsx-runtime"),xe=(0,a.getPreferenceValues)(),E=xe.brewPath&&xe.brewPath.length>0?xe.brewPath:(0,on.cpus)()[0].model.includes("Apple")?"/opt/homebrew/bin/brew":"/usr/local/bin/brew";async function L(e){let{stdout:t,stderr:n}=await en(e);return{stdout:t,stderr:n}}async function $(){if(!(0,rn.existsSync)(E))return await(0,a.showToast)(a.ToastStyle.Failure,"Brew Executable Not Found",`Is brew installed at ${E}?`),[];let t=(await L(`${E} services list`)).stdout.split(`
`);if(t.length<=1)return(0,a.showToast)(a.ToastStyle.Failure,"Error Parsing Service Data","There are no services."),[];for(let r=0;r<t.length-1;r++)if(t[r].startsWith("Name")){t.splice(0,r+1);break}let n=[];for(let r of t){let o=r.trim().split(/ +/g);if(o.length<2)return(0,a.showToast)(a.ToastStyle.Failure,"Error Parsing Service Data","Service data could not be parsed."),[];let i=o[1];i==="none"&&(i="stopped"),o.length!==4&&o[1]==="started"&&(i="running"),n.push({name:o[0],status:i,user:o.length===4?o[2]:"",path:o.at(-1)??""})}return n}async function tn(e){let t=new a.Toast({style:a.ToastStyle.Animated,title:"Stopping Service",message:`Stopping ${e}`});t.show(),await L(`${E} services stop ${e}`);let n=await $();for(let r of n)r.name===e&&(r.status==="stopped"?(t.style=a.ToastStyle.Success,t.title="Stopped Service",t.message=`Stopped ${e}`):(t.style=a.ToastStyle.Failure,t.title="Error Stopping Service",t.message=`${e} could not be stopped properly`))}async function Gr(e){let t=new a.Toast({style:a.ToastStyle.Animated,title:"Starting Service",message:`Starting ${e}`});t.show(),await L(`${E} services start ${e}`);let n=await $();for(let r of n)r.name===e&&(r.status==="started"?(t.style=a.ToastStyle.Success,t.title="Started Service",t.message=`Started ${e}`):(t.style=a.ToastStyle.Failure,t.title="Error Starting Service",t.message=`${e} could not be started properly`))}async function nn(e){let t=new a.Toast({style:a.ToastStyle.Animated,title:"Restarting Service",message:`Restarting ${e}`});t.show(),await L(`${E} services restart ${e}`);let n=await $();for(let r of n)r.name===e&&(r.status==="started"||r.status==="running"?(t.style=a.ToastStyle.Success,t.title="Restarted Service",t.message=`Restarted ${e}`):(t.style=a.ToastStyle.Failure,t.title="Error Restarting Service",t.message=`${e} could not be restarted properly`))}async function Rr(e){let t=new a.Toast({style:a.ToastStyle.Animated,title:"Running Service",message:`Running ${e}`});t.show(),await L(`${E} services run ${e}`);let n=await $();for(let r of n)r.name===e&&(r.status==="running"?(t.style=a.ToastStyle.Success,t.title="Ran Service",t.message=`Ran ${e}`):(t.style=a.ToastStyle.Failure,t.title="Error Running Service",t.message=`${e} could not be run properly`))}function $r(e){return e==="started"||e==="running"?{source:a.Icon.Checkmark,tintColor:a.Color.Green}:e==="stopped"?{source:a.Icon.XmarkCircle,tintColor:a.Color.Red}:{source:a.Icon.ExclamationMark,tintColor:a.Color.Yellow}}function Or(e){return e.data.status==="started"||e.data.status==="running"?(0,h.jsxs)(a.ActionPanel,{children:[(0,h.jsxs)(a.ActionPanel.Section,{title:"Manage Service",children:[(0,h.jsx)(a.ActionPanelItem,{title:"Stop Service",onAction:()=>tn(e.data.name)}),(0,h.jsx)(a.ActionPanelItem,{title:"Restart Service",onAction:()=>nn(e.data.name)})]}),(0,h.jsxs)(a.ActionPanel.Section,{title:"Plist",children:[(0,h.jsx)(a.ShowInFinderAction,{title:"Reveal Plist File in Finder",path:e.data.path}),(0,h.jsx)(a.CopyToClipboardAction,{title:"Copy Plist File Path",content:e.data.path})]})]}):e.data.status==="stopped"?(0,h.jsxs)(a.ActionPanel,{title:"Manage Service",children:[(0,h.jsx)(a.ActionPanelItem,{title:"Start Service",onAction:()=>Gr(e.data.name)}),(0,h.jsx)(a.ActionPanelItem,{title:"Run Service",onAction:()=>Rr(e.data.name)})]}):(0,h.jsxs)(a.ActionPanel,{title:"Manage Service",children:[(0,h.jsx)(a.ActionPanelItem,{title:"Stop Service",onAction:()=>tn(e.data.name)}),(0,h.jsx)(a.ActionPanelItem,{title:"Restart Service",onAction:()=>nn(e.data.name)})]})}function sn(e){return(0,h.jsx)(a.List,{isLoading:!e.services,searchBarPlaceholder:"Search for services...",children:(e.services??[]).map(t=>(0,h.jsx)(a.List.Item,{id:t.name,title:t.name,subtitle:t.status,accessoryTitle:t.user,icon:$r(t.status),actions:(0,h.jsx)(Or,{data:t})},t.name))})}var cn=require("react/jsx-runtime");function an(){let[e,t]=(0,V.useState)();return(0,V.useEffect)(()=>{$().then(n=>t(n))}),(0,cn.jsx)(sn,{services:e})}
