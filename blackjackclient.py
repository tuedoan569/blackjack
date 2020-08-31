from PodSixNet.Connection import ConnectionListener, connection
from time import sleep

import pygame
from pygame.locals import *

class Button:

    def __init__(self, image, x, y):
        self.image = image
        self.x = x
        self.y = y
        self.rect = self.image.get_rect(x=self.x, y=self.y)
        self.clicked = False

    def click(self, event):
        self.clicked = self.rect.collidepoint(event.pos)

class Card:

    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        self.image = pygame.transform.scale(pygame.image.load('resources/cards/' + suit + rank + '.gif'), (71, 96))

class Hand:
    
    def __init__(self):
        self.cards = []
        self.value = 0
        self.aces = 0

    def add_card(self,card):
        self.cards.append(card)

    def reset(self):
        self.cards.clear()

class BlackjackGame(ConnectionListener):

    def Network_close(self, data):
        exit()

    def Network_updatestatus(self, data):
        print(data)
        self.status = data["status"]
        self.outcome = data["outcome"]
        player_cards = data["player_cards"]
        dealer_cards = data["dealer_cards"]
        self.player_hand = self.deserializecards(player_cards)
        self.dealer_hand = self.deserializecards(dealer_cards)
        if self.status != 3:
            self.currentBet = data["currentBet"]
            self.chips = data["chips"]

    def Network_start(self, data):
        self.running=True

    def deserializecards(self, cards):
        hand = Hand()
        for card in cards:
            c = Card(card[0], card[1:])
            hand.add_card(c)
        return hand

    def update(self):
        clicked = False
        self.hitb.clicked = False
        self.standb.clicked = False
        self.betb.clicked = False
        self.doubleb.clicked = False
        self.chip1b.clicked = False
        self.chip2b.clicked = False
        self.chip3b.clicked = False
        self.chip4b.clicked = False
        self.chip5b.clicked = False

        #Clear Screen
        self.screen.blit(self.bgimage, (0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                clicked = True
                self.hitb.click(event)
                self.standb.click(event)
                self.betb.click(event)
                self.doubleb.click(event)
                self.chip1b.click(event)
                self.chip2b.click(event)
                self.chip3b.click(event)
                self.chip4b.click(event)
                self.chip5b.click(event)

        if self.status == 1: # in a turn(hit or stand)
            if self.hasDoubled == False: 
                self.screen.blit(self.hitb.image, (self.hitb.x, self.hitb.y))
            if self.hasDoubled == False:
                self.screen.blit(self.standb.image, (self.standb.x, self.standb.y))
            if self.chips >= self.currentBet and self.firstTurn:
                self.screen.blit(self.doubleb.image, (self.doubleb.x, self.doubleb.y))

            if self.hasDoubled == False and self.hitb.clicked:
                # player hit
                self.firstTurn = False
                self.Send({"action": "hit"})
            if self.hasDoubled == False and self.standb.clicked:
                # player stand
                self.firstTurn = False
                self.Send({"action": "stand"})
            if self.chips >= self.currentBet and self.firstTurn:
                if self.doubleb.clicked:
                    # player doubled
                    self.firstTurn = False
                    self.hasDoubled = True
                    self.Send({"action": "double"})

        elif self.status == 2: # game ended(wait for click)
            text = self.font.render(self.outcome, 1, (255, 255, 255))
            self.screen.blit(text, (40, 338))
            self.renderBetChips()

            if clicked == True:
                self.Send({"action": "endhand"})
        elif self.status == 3: # taking bet and pressing start
            self.firstTurn = True
            self.hasDoubled = False
            self.screen.blit(self.betb.image, (self.betb.x, self.betb.y))

            if self.betb.clicked:
                self.Send({"action": "bet", "bet": self.currentBet})
            if self.chip1b.clicked:
                if self.chips >= 10:
                    self.currentBet += 10
                    self.chips -= 10
            if self.chip2b.clicked:
                if self.chips >= 25:
                    self.currentBet += 25
                    self.chips -= 25
            if self.chip3b.clicked:
                if self.chips >= 50:
                    self.currentBet += 50
                    self.chips -= 50
            if self.chip4b.clicked:
                if self.chips >= 100:
                    self.currentBet += 100
                    self.chips -= 100
            if self.chip5b.clicked:
                if self.chips >= 500:
                    self.currentBet += 500
                    self.chips -= 500

        self.renderBetChips()
        self.screen.blit(self.chip1b.image, (self.chip1b.x, self.chip1b.y))
        self.screen.blit(self.chip2b.image, (self.chip2b.x, self.chip2b.y))
        self.screen.blit(self.chip3b.image, (self.chip3b.x, self.chip3b.y))
        self.screen.blit(self.chip4b.image, (self.chip4b.x, self.chip4b.y))
        self.screen.blit(self.chip5b.image, (self.chip5b.x, self.chip5b.y))

        for card in self.player_hand.cards:
            x = 530 + (self.player_hand.cards.index(card) * 75)
            self.screen.blit(card.image, (x, 350))

        if self.status == 1:
            if len(self.dealer_hand.cards) > 0:
                self.screen.blit(self.dealer_hand.cards[0].image, (530, 10))
                self.screen.blit(self.cardbackimage, (605, 10))
        else:
            for card in self.dealer_hand.cards:
                x = 530 + (self.dealer_hand.cards.index(card) * 75)
                self.screen.blit(card.image, (x, 10))
        
        pygame.display.update()

        connection.Pump()
        self.Pump()

    def renderBetChips(self):
        currentBetText = self.font.render("Bet: " + str(self.currentBet), 1, (225, 225, 225))
        currentChipsText = self.font.render("Chips: " + str(self.chips), 1, (225, 225, 225))
        self.screen.blit(currentBetText, (930, 338))
        self.screen.blit(currentChipsText, (930, 370))

    def __init__(self):
        self.status = 3
        self.running = False

        #1 Init Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((1204, 677))
        pygame.display.set_caption("Blackjack")
        self.font = pygame.font.SysFont("arial", 36)
        
        #2 Init Clock
        self.clock = pygame.time.Clock()

        #3 Init Graphics
        self.initGraphics()

        #4 Get server info and connect
        try:
            host, port="localhost", 8000
            self.Connect((host, int(port)))
        except:
            print("Error Connecting to Server")
            print("Usage:", "host:port")
            print("e.g. localhost:12345")
            exit()
        print("Blackjack Client Started")
        self.running=False
        self.owner=[[0 for x in range(6)] for y in range(6)]
        while not self.running:
            self.Pump()
            connection.Pump()

        #5 Init Blackjack Stuff
        self.player_hand = Hand()
        self.dealer_hand = Hand()
        self.chips = 10000
        self.currentBet = 0
        self.firstTurn = True
        self.hasDoubled = False

    def initGraphics(self):
        self.bgimage = pygame.image.load('resources/table.gif')
        self.cardbackimage = pygame.transform.scale(pygame.image.load('resources/cards/b2fv.gif'), (71, 96))

        hitbimage = pygame.transform.scale(pygame.image.load('resources/buttons/hit.gif'), (100, 45))
        self.hitb = Button(hitbimage, 442, 560)

        standbimage = pygame.transform.scale(pygame.image.load('resources/buttons/stand.gif'), (100, 45))
        self.standb = Button(standbimage, 550, 560)

        doublebimage = pygame.transform.scale(pygame.image.load('resources/buttons/double.gif'), (100, 45))
        self.doubleb = Button(doublebimage, 658, 560)

        betbimage = pygame.transform.scale(pygame.image.load('resources/buttons/bet.gif'), (100, 45))
        self.betb = Button(betbimage, 554, 560)

        chip1image = pygame.transform.scale(pygame.image.load('resources/chips/chip-1.gif'), (62, 72))
        self.chip1b = Button(chip1image, 448, 605)

        chip2image = pygame.transform.scale(pygame.image.load('resources/chips/chip-2.gif'), (62, 72))
        self.chip2b = Button(chip2image, 510, 605)

        chip3image = pygame.transform.scale(pygame.image.load('resources/chips/chip-3.gif'), (62, 72))
        self.chip3b = Button(chip3image, 572, 605)

        chip4image = pygame.transform.scale(pygame.image.load('resources/chips/chip-4.gif'), (62, 72))
        self.chip4b = Button(chip4image, 634, 605)

        chip5image = pygame.transform.scale(pygame.image.load('resources/chips/chip-5.gif'), (62, 72))
        self.chip5b = Button(chip5image, 696, 605)

bj=BlackjackGame()
while 1:
    if bj.update()==1:
        break
bj.finished()
