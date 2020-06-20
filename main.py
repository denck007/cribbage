
from Cribbage import Game,HandScorer
import time


if __name__ == "__main__":
    scorer = HandScorer()
    
    gamesToPlay = 100
    printEvery = int(gamesToPlay//10)

    startTime = time.time()
    player1Wins = 0
    for ii in range(gamesToPlay):
        handTime = time.time()
        game = Game("random","BestMinimalHandAndScorePegging",scorer=scorer,verbose=False)
        game.playGame()
        if game.player1Score > game.player2Score:
            player1Wins += 1
        handTime = time.time() - handTime
        elapsedTime = time.time() - startTime
        handTimeAvg = elapsedTime/(ii+1)
        remaining = (gamesToPlay - ii) / handTimeAvg
        p1WinRate = float(player1Wins)/(ii+1)*100
        if not ii%printEvery:
            print("Game {} Player1 win rate: {:.1f} Elapsed: {:.1f} Remaining: {:.1f} Average per hand: {:.3f}".format(ii, p1WinRate, elapsedTime, remaining, handTimeAvg))
        
    print("Player 1 won {}/{} games, {:.1f}%".format(player1Wins,gamesToPlay,float(player1Wins)/gamesToPlay*100.))

