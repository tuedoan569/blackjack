import PodSixNet.Channel
import PodSixNet.Server
 
from time import sleep

import random

suits = ['h', 'd', 's', 'c']
ranks = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'j', 'q', 'k']
values = {'1':11, '2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, '10':10, 'j':10, 'q':10, 'k':10}

class ClientChannel(PodSixNet.Channel.Channel):
    def Network(self, data):
        print(data)
    
    def Network_hit(self, data):
        self._server.clientHit()
    
    def Network_stand(self, data):
        self._server.clientStand()

    def Network_bet(self, data):
        self._server.clientBet(data)

    def Network_endhand(self, data):
        self._server.clientEndhand()

    def Network_double(self, data):
        self._server.clientDouble()

    def Close(self):
        self._server.close()

class BlackjackServer(PodSixNet.Server.Server):
    channelClass = ClientChannel

    def __init__(self, *args, **kwargs):
        PodSixNet.Server.Server.__init__(self, *args, **kwargs)
        self.game = None
        self.player = None

    def Connected(self, channel, addr):
        print("New Connection", channel)
        if self.player == None:
            self.player = channel
            self.game = Blackjack(self.player)
            self.player.Send({"action": "start"})
        else:
            channel.Send({"action": "close"})

    def clientHit(self):
        self.game.clientAction = 1

    def clientStand(self):
        self.game.clientAction = 2

    def clientEndhand(self):
        self.game.status = 8

    def clientBet(self, data):
        self.game.currentBet = data["bet"]
        self.game.status = 9

    def clientDouble(self):
        self.game.clientAction = 3

    def close(self):
        try:
            self.game = None
            self.player = None
            self.player.Send({"action":"close"})
        except:
            pass

    def tick(self):
        if self.game is not None:
            self.game.update()
        self.Pump()
            
class Blackjack:

    def __init__(self, player):
        self.chips = 10000
        self.currentBet = 0
        self.player = player
        self.status = 8
        self.clientAction = 0
        self.deck = Deck()
        self.player_hand = Hand()
        self.dealer_hand = Hand()

    def serializecards(self, hand):
        cards = []
        for card in hand.cards:
            cards.append(card.suit + card.rank)
        return cards

    def update(self):
        if self.status == 0: # dealing
            self.deck = Deck()
            self.deck.shuffle()

            self.player_hand.reset()
            self.player_hand.add_card(self.deck.deal())
            self.player_hand.add_card(self.deck.deal())

            self.dealer_hand.reset()
            self.dealer_hand.add_card(self.deck.deal())
            self.dealer_hand.add_card(self.deck.deal())

            if self.dealer_hand.value == 21:
                self.status = 4
            elif self.player_hand.value == 21:
                self.status = 5
            else:
                self.status = 1
                self.player.Send({"action": "updatestatus", "status":1, "outcome": " ", "player_cards": self.serializecards(self.player_hand), "dealer_cards": self.serializecards(self.dealer_hand), "chips": self.chips, "currentBet": self.currentBet})
        elif self.status == 1 and self.clientAction == 1: # in turn and client hit\
            self.player_hand.add_card(self.deck.deal())
            if self.player_hand.value > 21:
                self.status = 2
                self.clientAction = 0
            elif self.player_hand.value == 21:
                self.clientAction = 2
            else:
                self.player.Send({"action": "updatestatus", "status":1, "outcome": " ", "player_cards": self.serializecards(self.player_hand), "dealer_cards": self.serializecards(self.dealer_hand), "chips": self.chips, "currentBet": self.currentBet})
                self.clientAction = 0
        elif self.status == 1 and self.clientAction == 2: # in turn and client stood
            # player standing
            while self.dealer_hand.value <= 16:
                self.dealer_hand.add_card(self.deck.deal())
            if self.dealer_hand.value > 21:
                self.status = 6
            elif self.dealer_hand.value > self.player_hand.value:
                self.status = 7
            else:
                self.status = 6
            self.clientAction = 0
        elif self.status == 1 and self.clientAction == 3: # client doubled
            self.chips -= self.currentBet
            self.currentBet += self.currentBet
            self.player_hand.add_card(self.deck.deal())
            if self.player_hand.value > 21:
                self.status = 2
                self.clientAction = 0
            else:
                self.clientAction = 2
        elif self.status == 2: #busted
            self.currentBet = 0
            self.player.Send({"action": "updatestatus", "status":2, "outcome": "Busted!", "player_cards": self.serializecards(self.player_hand), "dealer_cards": self.serializecards(self.dealer_hand), "chips": self.chips, "currentBet": self.currentBet})
            self.status = 10
        elif self.status == 4: #dealer blackjack
            self.currentBet = 0
            self.player.Send({"action": "updatestatus", "status":2, "outcome": "Dealer Blackjack!", "player_cards": self.serializecards(self.player_hand), "dealer_cards": self.serializecards(self.dealer_hand), "chips": self.chips, "currentBet": self.currentBet})
            self.status = 10
        elif self.status == 5: #player blackjack
            self.chips += (self.currentBet + (self.currentBet * 1.5))
            self.currentBet = 0
            self.player.Send({"action": "updatestatus", "status":2, "outcome": "Player Blackjack!", "player_cards": self.serializecards(self.player_hand), "dealer_cards": self.serializecards(self.dealer_hand), "chips": self.chips, "currentBet": self.currentBet})
            self.status = 10
        elif self.status == 6: #player win
            self.chips += (self.currentBet * 2)
            self.currentBet = 0
            self.player.Send({"action": "updatestatus", "status":2, "outcome": "You Won!", "player_cards": self.serializecards(self.player_hand), "dealer_cards": self.serializecards(self.dealer_hand), "chips": self.chips, "currentBet": self.currentBet})
            self.status = 10
        elif self.status == 7: #player lost
            self.currentBet = 0
            self.player.Send({"action": "updatestatus", "status":2, "outcome": "You Lost!", "player_cards": self.serializecards(self.player_hand), "dealer_cards": self.serializecards(self.dealer_hand), "chips": self.chips, "currentBet": self.currentBet})
            self.status = 10
        elif self.status == 8: #resetting, taking bet
            print("status8")
            self.player_hand.reset()
            self.dealer_hand.reset()
            self.player.Send({"action": "updatestatus", "status":3, "outcome": " ", "player_cards": self.serializecards(self.player_hand), "dealer_cards": self.serializecards(self.dealer_hand), "chips": self.chips, "currentBet": self.currentBet})
        elif self.status == 9:
            print("status9")
            self.chips -= self.currentBet
            self.status = 0

class Card:

    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

class Deck:

    def __init__(self):
        self.deck = []
        for suit in suits:
            for rank in ranks:
                self.deck.append(Card(suit,rank))

    def shuffle(self):
        random.shuffle(self.deck)

    def deal(self):
        single_card = self.deck.pop()
        return single_card

class Hand:
    
    def __init__(self):
        self.cards = []
        self.value = 0
        self.aces = 0

    def add_card(self,card):
        print(card.rank)
        self.cards.append(card)
        self.value += values[card.rank]
        if card.rank == '1':
            print("found an ace")
            self.aces += 1
        self.adjust_for_ace()

    def adjust_for_ace(self):
        while self.value > 21 and self.aces:
            self.value -= 10
            self.aces -= 1
            print("adjusted an ace")

    def reset(self):
        self.cards.clear()
        self.value = 0
        self.aces = 0

print("Starting Blackjack Server")

host, port="localhost", 8000
blackjackserve=BlackjackServer(localaddr=(host, int(port)))
while True:
    blackjackserve.tick()