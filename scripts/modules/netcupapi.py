import requests
import re


class NetcupAPI:

    netcupAPIUrl = ""
    netcupUser = ""
    netcupPassword = ""
    failoverIP = ""
    failoverIPNetmask = ""

    def __init__(self, netcupAPIUrl, netcupUser, netcupPassword, failoverIP, failoverIPNetmask):
        self.netcupAPIUrl = netcupAPIUrl
        self.netcupUser = netcupUser
        self.netcupPassword = netcupPassword
        self.failoverIP = failoverIP
        self.failoverIPNetmask = failoverIPNetmask

    def hasServerFailoverIP(self, server):
        # Template
        #
        template_message = """<?xml version="1.0" encoding="UTF-8"?>
                            <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns1="http://enduser.service.web.vcp.netcup.de/">
                                    <SOAP-ENV:Body>
                                            <ns1:getVServerIPs>
                                                    <loginName>%s</loginName>
                                                    <password>%s</password>
                                                            <vserverName>%s</vserverName>
                                                    </ns1:getVServerIPs>
                                    </SOAP-ENV:Body>
                            </SOAP-ENV:Envelope>"""
        # create Message
        message = template_message % (
            self.netcupUser, self.netcupPassword,  server.netcupServerName)

        # header definition
        headers = {"Content-Type":  "text/xml ; charet=UTF-8",
                   "Content-Length": str(len(message)), "SOAPAction": ""}

        # send SOAP Post request
        response = requests.post(
            self.netcupAPIUrl, data=message, headers=headers)
        if self.failoverIP in response.text:
            return True
        else:
            return False

    def changeIPRouting(self, server, netmask='00:00:00:00:00:00'):
        # Template
        template_message = """<?xml version="1.0" encoding="UTF-8"?>
                <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns1="http://enduser.service.web.vcp.netcup.de/">
                    <SOAP-ENV:Body>
                        <ns1:changeIPRouting>
                            <loginName>%s</loginName>
                            <password>%s</password>
                                <routedIP>%s</routedIP>
                                <routedMask>%s</routedMask>
                                <destinationVserverName>%s</destinationVserverName>
                                <destinationInterfaceMAC>%s</destinationInterfaceMAC>
                            </ns1:changeIPRouting>
                    </SOAP-ENV:Body>
                </SOAP-ENV:Envelope>"""
        # Create Message
        message = template_message % (
            self.netcupUser, self.netcupPassword, server.ip, netmask, server.netcupServerName, server.mac)

        # header definition
        headers = {"Content-Type":  "text/xml ; charet=UTF-8",
                   "Content-Length": str(len(message)), "SOAPAction": ""}

        # Send SOAP Post
        response = requests.post(
            self.netcupAPIUrl, data=message, headers=headers)
        if response.status_code == 200:
            #self.logger.info("SOAP: changeIPRouting Returncode 200.")
            status = re.search(r'<return>(.*?)<\/return>', response.content)
            if status:
                return status.group(1)  # true
            else:
                return response.content
        else:
            return response.content