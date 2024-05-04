import logging
import os
from modules.netcupapi import NetcupAPI
from modules import helper
from modules.vserver import VServer
import requests
import sys
import time

# init logging
logFile = '/var/log/failover.log'
logFormat = '%(asctime)s - %(levelname)s - %(message)s'
logLevel = os.environ["LOG_LEVEL"]

# Init Logger
logger = helper.initLogging(logFormat, logLevel, logFile)


# check parameter
###################################
if not helper.checkParameterAvailable():
    sys.exit(1)
elif not (helper.checkIPFormat(os.environ['FAILOVER_IP'])):
    logger.error('Wrong format for parameter FAILOVER_IP...Abort')
    sys.exit(1)


#####     PARAMETER     #####
netcupAPIUrl = os.environ["NETCUP_API_URL"]
netcupUser = os.environ["NETCUP_USER"]
netcupPassword = os.environ["NETCUP_PASSWORD"]
failoverIP = os.environ["FAILOVER_IP"]
failoverIPNetmask = os.environ["FAILOVER_NETMASK"]
isDryRun = os.environ["DRY_RUN"]
logger.debug(isDryRun)

webhookURL = os.environ['WEBHOOK_URL']
timeBetweenPings = int(os.environ["TIME_BETWEEN_PINGS"])

# create netcupAPI object
netcupAPI = NetcupAPI(netcupAPIUrl, netcupUser, netcupPassword,
                      failoverIP, failoverIPNetmask, logger)

# read failover server
failoverServers = netcupAPI.getAllFailoverServers()

logger.info("FailoverIP monitoring is active ...")
while True:

    # failoverIP is reachable --> no action
    if netcupAPI.isFailoverIPPingable(timeBetweenPings):
        # wait 10 sec
        time.sleep(10)
        continue

    # failover ip is unreachable
    logger.warning('FailoverIP unreachable, check server ...')

    # get first pingable server
    firstPingableServer = netcupAPI.getFirstPingableServer(failoverServers)
    logger.info('First reachable server is ' +
                firstPingableServer.nickname)

    # get current failover server
    currentFailoverIPServer = netcupAPI.getCurrentIPFailoverServer(
        failoverServers)

    if netcupAPI.isPingable(currentFailoverIPServer.ipAddress):
        # current assigned failoverIP server is reachable --> no action (netcup infrastcuture problem)
        logger.info(
            'Current failover server is reachable, failoverIP will not switched ...')
        continue

    if not netcupAPI.isNetcupAPIReachable():
        # current assigned failoverIP server is reachable --> no action (netcup infrastcuture problem)
        logger.info(
            'Netcup SCP API is unreachable, failoverIP cannot be swiched ... ')
        continue

    if isDryRun == 'ENABLED':
        # dry run is enabled
        logger.info('Dry Run is enabled, no action ...')
        continue

    if currentFailoverIPServer is None:
        #FailoverIP is not assigned
        logger.warning('FailoverIP is not assigned. Assign to ' +
                    firstPingableServer.nickname)
        netcupAPI.setFailoverIPRouting(firstPingableServer)
        logger.info('FailoverIP assigned, continue monitoring...')
        time.sleep(10)
        continue
    else:
        logger.info('Current failover server is ' +
                    currentFailoverIPServer.nickname)

    def send_webhook_message(webhook_url, message, status='failed'):
        try:
            response = requests.post(webhook_url, json={'message': message, 'status': status})
            response.raise_for_status()
        except requests.RequestException as error:
            logger.error(f"Failed to send webhook message: {str(error)}")

#######    FAILOVER    #######
    # delete IP Routing
    logger.info("Delete FailoverIP from " + currentFailoverIPServer.nickname + " ... ")
    if netcupAPI.deleteFailoverIPRouting(currentFailoverIPServer):
        logger.info("FailoverIP routing deleted...")
        logger.info("Set new FailoverIP routing to " + firstPingableServer.nickname + " ... ")
        if netcupAPI.setFailoverIPRouting(firstPingableServer):
            send_webhook_message(webhookURL, 'Failover successful from ' + currentFailoverIPServer.nickname + ' to ' + firstPingableServer.nickname, 'success')
        else:
            logger.error('Error in new Routing ... Restart')
            send_webhook_message(webhookURL, 'Error in Failover ...')
    else:
        send_webhook_message(webhookURL, 'Error in Failover ...')
