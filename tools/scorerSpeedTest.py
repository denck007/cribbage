'''
Look at how different cache strategies change effectiveness of 
    the cache
'''

from Cribbage.cribbage import HandScorer,Deck

import matplotlib.pyplot as plt
import numpy as np
from itertools import combinations
import time
import json
import os

def movingAverage(data,n):

    output = np.zeros_like(data).astype(np.float32)
    total = np.cumsum(data)
    output[n:] = total[n:] - total[:-n]
    output[n:] = output[n:]/n
    output[1:n] = total[1:n]/np.arange(1,n,1)
    output[0] = data[0]
    return output

def exponentialMovingAverage(data,factor):

    output = np.copy(data)
    for idx in range(1,output.shape[0]):
        output[idx] = factor*output[idx-1] + (1-factor)*output[idx]

    return output

generateData = False

deck = Deck()

modes = {"No Cache": {"useCacheLarge":False,"useCache15":False,"useCachePair":False,"useCacheStraight":False},
        "All Caches": {"useCacheLarge":True,"useCache15":True,"useCachePair":True,"useCacheStraight":True},
        "No Large": {"useCacheLarge":False,"useCache15":True,"useCachePair":True,"useCacheStraight":True},
        "Only Large": {"useCacheLarge":True,"useCache15":False,"useCachePair":False,"useCacheStraight":False}}

if generateData:
    for mode,props in modes.items():
        print(mode)
        modeAverage = None
        for ii in range(5):
            scorer = HandScorer(**props)

            times =[.01]
            ema = [.01]
            emaFactor = .9
            runStart = time.time()
            for jj in range(1000):
                startTime = time.time()
                deck.shuffle()
                hand = deck.getCards(6)
                for combination in combinations(hand,4):
                    for turn in deck.cards:
                        score = scorer(list(combination),turn)
                elapsed = time.time() - startTime
                times.append(elapsed)
                ema.append(ema[-1]*emaFactor + elapsed*(1-emaFactor))

            if modeAverage is None:
                modeAverage = ema[-1]
            else:
                modeAverage = (modeAverage*(ii) + ema[-1]) / (ii+1)
            print("\tIteration {:4d} time: {:.5f} Current Average: {:.5f}".format(ii, ema[-1],modeAverage))


            #print("Run time {:20s}: {:.5f}".format(mode,time.time()-runStart))

            fname = "{}_timings.json".format(mode)
            if os.path.isfile(fname):
                with open(fname,'r') as fp:
                    data = json.load(fp)
                    data.update({int(time.time()):times})
            else:
                data = {int(time.time()):times}
            with open(fname,'w') as fp:
                json.dump(data,fp,indent=2)



colors = ['r','g','b','k']
for modeIdx, mode in enumerate(modes):
    mins = []
    maxs = []
    totals = []
    counts = []
    avg = []

    print(mode)
    with open("{}_timings.json".format(mode),'r') as fp:
        dataRaw = json.load(fp)
    
    for runId, values in dataRaw.items():
        for idx,value in enumerate(values):
            if len(counts) <= idx:
                counts.append(1)
                mins.append(value)
                maxs.append(value)
                totals.append(value)
            else:
                counts[idx] += 1
                mins[idx] = min(mins[idx],value)
                maxs[idx] = max(maxs[idx],value)
                totals[idx] += value

    avg = np.array(totals,dtype=np.float32)/np.array(counts,dtype=np.float32)

    ma = movingAverage(avg[1:],100)
    emaFactor = .999
    ema = exponentialMovingAverage(avg[1:],emaFactor)
    ema_min = exponentialMovingAverage(np.array(mins[1:],dtype=np.float32),emaFactor)
    ema_max = exponentialMovingAverage(np.array(maxs[1:],dtype=np.float32),emaFactor)

    plt.plot(ema,label=mode,c=colors[modeIdx])
    plt.plot(ema_min,c=colors[modeIdx],linewidth=1,alpha=.5)
    plt.plot(ema_max,c=colors[modeIdx],linewidth=1,alpha=.5)


plt.legend(loc='upper right')
plt.show()

'''
plt.subplot(2,2,1)
plt.title("Pairs Hit")
ma = movingAverage(scorer.hitPair,100)
plt.plot(scorer.hitPair,label="Actual")
plt.plot(ma,label="Average")
plt.legend(loc='upper right')

plt.subplot(2,2,3)
plt.title("Pairs Times")
plt.plot(scorer.timePair,label="Actual")
ma = movingAverage(scorer.timePair,100)
plt.plot(ma,label="Average")
plt.legend(loc='upper right')
plt.plot()


plt.subplot(2,2,2)
plt.title("15s Hit")
ma = movingAverage(scorer.hit15,100)
plt.plot(scorer.hit15,label="Actual")
plt.plot(ma,label="Average")
plt.legend(loc='upper right')

plt.subplot(2,2,4)
plt.title("15s Times")
plt.plot(scorer.time15,label="Actual")
ma = movingAverage(scorer.time15,100)
plt.plot(ma,label="Average")
plt.legend(loc='upper right')
plt.plot()
plt.show()

'''
