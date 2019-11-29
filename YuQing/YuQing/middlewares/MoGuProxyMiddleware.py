# 代理服务器
proxyServer = "http://secondtransfer.moguproxy.com:9001"
proxy = {"http": "http://" + proxyServer, "https": "https://" + proxyServer}

# appkey为你订单的key
proxyAuth = "Basic " + "VU9WOUh1ZXM2bzBVbWVPcTpjQ3EybHplNnI3TXJLT21E"  # 这一长串是你的Key


class MoGuProxyMiddleware(object):
    """蘑菇代理中间件"""

    def process_request(self, request, spider):
        request.meta["proxy"] = proxyServer
        request.headers["Authorization"] = proxyAuth

    def process_response(self, request, response, spider):
        '''对返回的response处理'''
        # 如果返回的response状态不是200，重新生成当前request对象

        if response.status != 200:
            request.meta["proxy"] = proxyServer
            request.headers["Authorization"] = proxyAuth
            return request

        return response