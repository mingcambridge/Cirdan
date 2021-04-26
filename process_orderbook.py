"""

This module contains the implementation of order and orderbook, 
and the function to process orders and get best bid and ask prices. 


"""


from collections import defaultdict
import decimal
import logging

#Available logging mode list, CRITICAL, ERROR, WARNING, INFO ,DEBUG.
logging.basicConfig(level=logging.WARNING)

# Length of orders
CANCEL_ORDER_LEN = 3
UPDATE_ORDER_LEN = 4
NEW_ORDERE_LEN = 7

# Index of fields in order
ORDERID_INDEX = 1
ACTION_INDEX = 2
TICKER_INDEX = 3
SIDE_INDEX = 4
PRICE_INDEX = 5
NEW_ORDER_SIZE_INDEX = 6
UPDATE_ORDER_SIZE_INDEX = 3

# Action fields 
ACTION_NEW_ORDER = 'a'
ACTION_CANCEL_ORDER = 'c'
ACTION_UPDATE_ORDER = 'u'

delimiter = '|'


class Order:
    ''' Class to represent the order
    '''
    def __init__(self, orderId, ticker, side, price, size):
        self._orderId = orderId
        self._ticker = ticker
        self._side = side
        self._size = int(size)
        self._price = float(price)
  
    def __str__(self):
        return "|".join([self._orderId, self._ticker, self._side,
                    "{0:.5f}".format(self._price), "{0}".format(self._size)])

    def Size(self, size=None):
        if size:
            self._size = int(size)
        return self._size
 
    def OrderId(self):
        return self._orderId
   
    def Ticker(self):
        return self._ticker
    
    def Price(self):
        return self._price
        
    def Side(self):
        return self._side
       
class OrderBook:
    ''' Class to represent the order book
    '''
    
    def __init__(self):
        self._books = {}
        self._tickerOrderIds = defaultdict(list)

    def _isValidOrder(self, order):
        ''' Method to validate an order
        '''
        try:
            lOrder = len(order)
            if lOrder not in (CANCEL_ORDER_LEN, UPDATE_ORDER_LEN, NEW_ORDERE_LEN):
                logging.warning("Wrong order length {0}, for order {1}".format(lOrder, delimiter.join(order)))
                return False
    
            action = order[ACTION_INDEX]
            if lOrder == CANCEL_ORDER_LEN and action == ACTION_CANCEL_ORDER:
                return True
            if lOrder == UPDATE_ORDER_LEN and action == ACTION_UPDATE_ORDER:
                return True

            if lOrder == NEW_ORDERE_LEN:
                if action != ACTION_NEW_ORDER:
                    logging.warning("Invalid action {0} for order {1}".format(action, delimiter.join(order)))
                    return False
                side = order[SIDE_INDEX]
                if side not in ['B', 'S']:
                    logging.warning("Invalid Side {0} for order {1}".format(side, delimiter.join(order)))
                    return False
                price = decimal.Decimal(order[PRICE_INDEX])
                if abs(price.as_tuple().exponent) > 5:
                    logging.warning("Wrong price formate {0} for order {1}".format(price, delimiter.join(order)))
                    return False
                size = int(order[NEW_ORDER_SIZE_INDEX])
                if size <= 0:
                    logging.warning("Wrong size {0} for order {1}".format(size, delimiter.join(order)))
                    return False
            return True
        except Exception as err:
            logging.error("Caught a exception in _isValidOrder, err {0}".format(str(err)))
        return False
    
    def getOrder(self, orderId):
        ''' Method to retrieve the order by ID
        '''
        return self._books.get(orderId, None)

    def _new_order(self, existingOrder, ordDetails, order):
        ''' Method to create new order
        '''
        orderId = ordDetails[ORDERID_INDEX].strip()
        if existingOrder:
            logging.warning("Wrong add action for order {0}, the order id {1} is " \
              "already in the order book".format(order, orderId))
            return False
        ticker = ordDetails[TICKER_INDEX]
        self._books[orderId] = Order(orderId, ticker, ordDetails[SIDE_INDEX],
                                    ordDetails[PRICE_INDEX], ordDetails[NEW_ORDER_SIZE_INDEX])
        self._tickerOrderIds[ticker].append(orderId)
        return True


    def _cancel_order(self, existingOrder, ordDetails, order):
        ''' Method to cancel an order
        '''
        orderId = ordDetails[ORDERID_INDEX].strip()
        if not existingOrder:
            logging.warning("Wrong cancel action for order {0}, there is no order with " \
              "id {1} is in the order book".format(order, orderId))
            return False
    
        cancelOrdTickerID = existingOrder.Ticker()
        cancelOrderId = existingOrder.OrderId()
        
        orderIdList = self._tickerOrderIds.get(cancelOrdTickerID, [])
        if cancelOrderId not in self._tickerOrderIds[cancelOrdTickerID]:
              logging.error("Error! No order ID {0} found in the tickerOrderIds map for "\
                    "ticker {1}".format(cancelOrderId, cancelOrdTickerID))
              return False

        #remove the order from the book and ticker map
        del self._books[cancelOrderId]
        self._tickerOrderIds[cancelOrdTickerID].remove(cancelOrderId)
        return True


    def _update_order(self, existingOrder, ordDetails, order):
        ''' Method to update an order
        '''
        orderId = ordDetails[ORDERID_INDEX].strip()
        if not existingOrder:
            logging.error("Wrong update action for order {0}, there is no order with " \
              "ID {1} is in the order book".format(order, orderId))
            return False
        existingOrder.Size(int(ordDetails[UPDATE_ORDER_SIZE_INDEX]))
        return True


    def update_dispatcher(self, action, existingOrder, ordDetails, order):
        return {
            ACTION_NEW_ORDER: self._new_order,
            ACTION_CANCEL_ORDER: self._cancel_order,
            ACTION_UPDATE_ORDER: self._update_order,
            }.get(action, lambda a, b, c: False)(existingOrder, ordDetails, order)

    def update(self, order):
        ''' Method to update orderbook with a given order
        '''
        try:
            ordDetails = order.split(delimiter)
            if not self._isValidOrder(ordDetails):
                return False

            orderId = ordDetails[ORDERID_INDEX].strip()
            action = ordDetails[ACTION_INDEX].strip()
            existingOrder = self._books.get(orderId, None)
            return self.update_dispatcher(action, existingOrder, ordDetails, order)

        except Exception as err:
            logging.error("Caught an exception, err {0}".format(str(err)))
        return False
 
    def getTickerOrders(self, ticker):
        ''' Method to the orders by ticker 
        '''
        return self._tickerOrderIds[ticker]

    def printOrderBook(self):
        ''' Method to print orderbook
        '''
        for _, oItems in self._books.items():
            logging.info(oItems)


def processOrder(orderbook, order):
    ''' function to add, update or cancel an order in the order book
    '''
    return orderbook.update(order)
    

def getBestBidAndAsk(orderbook, ticker):
    ''' function to get te best bid and ask for the specified ticker
        If no tcket is present, return 0 for both bid and ask
    '''
    bid = 0.0
    ask = 0.0
    tickerOrders = orderbook.getTickerOrders(ticker)
    if not tickerOrders:
        return bid, ask
    
    for orderId in tickerOrders:
        order = orderbook.getOrder(orderId)
        if not order:
            logging.warning("No order ID {0} is found in the order book".format(orderId))
            continue

        if order.Side() == 'B':
            bid = order.Price() if bid == 0.0 else max(bid, order.Price())
        elif order.Side() == 'S':
            ask = order.Price() if ask == 0.0 else min(ask, order.Price())

    return bid, ask
 