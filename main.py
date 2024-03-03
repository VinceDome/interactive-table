import cv2, time, math, random, os
import numpy as np
from PIL import ImageFont, ImageDraw, Image

yogaSize = (1366, 768)
screenSize = (1920, 1080)

testradius=1
testwidth=30

running = True

#deklarálni kell őket ha nem szeretnénk aláhúzást, akkor is ha közvetlenül utána definiálom őket
webcam = None
guessTime = None
questions = None
displayTime = None
minR = None
maxR = None
errorMargin = None
squareSize = None
selectionTime = None

class Location:
    def __init__(self, loc):
        self.name, self.coords = loc.split("//")
        self.coords = self.coords.split(",")
        self.coords[0], self.coords[1] = int(self.coords[0]), int(self.coords[1])

class Guess:
    def __init__(self, dist, center, radius):
        self.dist = dist
        self.center = center
        self.radius = radius

def DetectCircles(source):
    insideCircles = cv2.HoughCircles(
    source,                  # Bemeneti kép
    cv2.HOUGH_GRADIENT,    # Detekciós módszer
    dp=1,                  # Képméretarány
    minDist=20+80,            # Minimum távolság két kör között
    param1=50,             # Canny élek paraméter
    param2=30,             # A Hough transzformáció küszöbértéke
    minRadius=minR,          # Minimum kör sugara
    maxRadius=maxR          # Maximum kör sugara
    )

  
    # Ellenőrizze, hogy talált-e köröket
    if insideCircles is not None:
        # Körök koordinátáinak kinyerése
        return np.uint16(np.around(insideCircles))

def text_utf(image, string, loc, size):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(image)

    # Draw non-ascii text onto image
    font = ImageFont.truetype("C:\Windows\Fonts\\arial.ttf", size)
    draw = ImageDraw.Draw(pil_image)
    draw.text(loc, string, font=font)

    # Convert back to Numpy array and switch back from RGB to BGR
    image = np.asarray(pil_image)
    return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

def CenteredText(image, string, loc, size, color, thickness):
    textsize = cv2.getTextSize(string, cv2.FONT_HERSHEY_COMPLEX, size, thickness)[0]

    loc = (int(loc[0]-(textsize[0]/2)), int(loc[1]+(textsize[1]/2)))
    
    cv2.putText(image, string, loc, cv2.FONT_HERSHEY_COMPLEX, size, color, thickness)
    return image

with open("parameters.txt", "r", encoding="utf-8") as file:
    for i in file:
        exec(i.strip())

with open("allocations.txt", "r", encoding="utf-8") as file:
    allLocations = file.read().split("\n")


if webcam==0: #integrált cam
    cap = cv2.VideoCapture(webcam)
    cap.set(3, 1920)
    cap.set(4, 1080)

elif webcam==1: #amikor van logitech akkor az, ha nincs akkor OBS
    cap = cv2.VideoCapture(webcam, cv2.CAP_DSHOW)
    cap.set(3, 1280)
    cap.set(4, 720)

elif webcam==2: # OBS
    cap = cv2.VideoCapture(webcam)
    cap.set(3, 1280)
    cap.set(4, 720)

#térkép betöltése
megyek = cv2.imread("megyek.png")
megyek = cv2.resize(megyek, screenSize)

#ablak kreálás
cv2.namedWindow("Webkamera", cv2.WINDOW_NORMAL)

#az ablaknak a mozgatása a projektor másodlagos képernyőjére 
cv2.moveWindow("Webkamera", yogaSize[0], 0)

#fulscreen
cv2.setWindowProperty("Webkamera", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cv2.imshow("Webkamera", megyek)
cv2.waitKey(1)



while running:
    playerGuesses = []
    chosenLocations = []

    while True:

        megyekT = megyek.copy()
        ret, frame = cap.read()
        #check ha hiba
        if not ret:
            print("Hiba a kép beolvasásakor")
            break

        #gray
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        #gray upscale
        gray = cv2.resize(gray, screenSize)
        #clear screen
        screen = megyekT.copy()

        circles = DetectCircles(gray)
        if circles is None:
            continue
        
        benne = None
        loc = False
        for circle in circles[0, :]:
            center = (circle[0], circle[1])
            radius = circle[2]
            cv2.circle(screen, center, radius+5, (0, 0, 255), 3)
            if (200 > center[0] > 100) and (500 > center[1] > 100):
                benne = True
                loc = center[1]

        cv2.rectangle(screen, (100, 50), (200, 500), (255, 0, 0), 10)
        cv2.line(screen, (150, 50), (150, 500), (255, 0, 0), 5)
        if benne:
            cv2.circle(screen, (150, loc), 15, (0, 155, 0), 5)
        cv2.imshow('Webkamera', screen)
        cv2.waitKey(1)

    #kérdések kisorsolása egy listába
    for i in range(questions):
        chosenLocations.append(Location(random.choice(allLocations)))

    for location in chosenLocations:

        #létrehozok egy alaphátteret, így nem kell minden kamerafeldolgozásnál kiírni az adott helyszín nevét
        megyekT = megyek.copy()
        #cv2.putText(megyekT, location.name, (500, 150), cv2.FONT_HERSHEY_COMPLEX, 5, (255, 0, 0), 20)
        CenteredText(megyekT, location.name, (screenSize[0]/2, 100), 5, (255, 0, 0), 20)
        #megyekT=text_utf(megyekT, "áááééőőóóüüöúű", (500, 150), 90)

        st = time.perf_counter()
        dists = []

        while time.perf_counter() < st + guessTime:
            # Kép beolvasása a webkamerából
            ret, frame = cap.read()
            #check ha hiba
            if not ret:
                print("Hiba a kép beolvasásakor")
                break

            #gray
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            #gray upscale
            gray = cv2.resize(gray, screenSize)
            #clear screen
            screen = megyekT.copy()

            cv2.putText(screen, str(round((st+guessTime-time.perf_counter()))), (100, 300), cv2.FONT_HERSHEY_SIMPLEX, 5, (255, 0, 0), 20)
            
            circles = DetectCircles(gray)
            if circles is None:
                continue

            closest = False
            #összes körön végigmenni
            for circle in circles[0, :]:
                center = (circle[0], circle[1])
                radius = circle[2]

                #utolsó fél másodperc, az összes távolságot elmentem, amiből kiválasztom a legközelebbit
                if time.perf_counter() > st + guessTime - 0.5:
                    dist = int(math.dist(location.coords, center))
                    
                    if not closest: 
                        closest = Guess(dist, center, radius)
                    elif dist < closest.radius:
                        closest = Guess(dist, center, radius)
                
                cv2.circle(screen, center, radius+5, (0, 0, 255), 3)
                #cv2.circle(megyek, center, testradius, (0, 0, 255), testwidth)
                
    
                
            # Kijelzés a képernyőn
        
            #képfrissítés
            cv2.imshow('Webkamera', screen)
            
            # Kilépés a 'q' lenyomásával
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            elif closest:
                #hozzáadom az iteráció legközelebbi távolságát
                dists.append(closest)
        if not dists:
            best = False
        else:
            best = min(dists, key=lambda x: x.dist)
            best.dist = max(best.dist-errorMargin, 0)

        playerGuesses.append(best)

        #displaying result immediately
        wt = time.perf_counter()
        
        while time.perf_counter() < wt + displayTime:
            screen = megyekT.copy()
            
            if best:
                cv2.line(screen, best.center, location.coords, (0,255,0), 10)

                cv2.circle(screen, best.center, best.radius, (0, 255, 0), 30)
                cv2.circle(screen, location.coords, testradius, (0, 0, 255), 20)

                
                CenteredText(screen, f"Distance: {best.dist}", (screenSize[0]/2, 950), 3, (255, 0, 0), 10)
            else:
                CenteredText(screen, "No guess!", (screenSize[0]/2, 950), 3, (255, 0, 0), 10)

            cv2.putText(screen, str(round((wt+displayTime-time.perf_counter()))), (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 5, (255, 0, 0), 20)

            
            cv2.imshow('Webkamera', screen)
            cv2.waitKey(1)

            time.sleep(0.5)



    screen = megyek.copy()

    totalDistance = 0

    for playerGuess, loc in zip(playerGuesses, chosenLocations):
        if playerGuess:
            print(playerGuess.center, playerGuess.dist, loc.coords, loc.name)
            cv2.line(screen, playerGuess.center, loc.coords, (0,255,0), 10)
            cv2.circle(screen, playerGuess.center, playerGuess.radius, (0, 255, 0), 30)
            cv2.circle(screen, loc.coords, testradius, (0, 0, 255), 20)
            totalDistance += playerGuess.dist

    #cv2.putText(screen, f"Total distance: {totalDistance}", (400,900), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 0, 0), 20)
    CenteredText(screen, f"Total distance: {totalDistance}", (screenSize[0]/2, 950), 3, (255, 0, 0), 10)
    megyekT = screen.copy()
    cv2.imshow('Webkamera', screen)
    cv2.waitKey(1)

    selecting = True
    lefttime = None
    righttime = None
    

    while selecting:
        #összes körön végigmenni
        ret, frame = cap.read()
        #check ha hiba
        if not ret:
            print("Hiba a kép beolvasásakor")
            break
        screen = megyekT.copy()
        #gray
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        #gray upscale
        gray = cv2.resize(gray, screenSize)

        left = (255,0,0)
        right = (255,0,0)

        circles = DetectCircles(gray)
        if circles is not None:
           
            for circle in circles[0, :]:
                center = (circle[0], circle[1])
                radius = circle[2]
                cv2.circle(screen, center, radius+5, (0, 0, 255), 3)
                
                #ha benne van a bal téglalapban
                if (squareSize > center[0] > 0) and (screenSize[1] > center[1] > screenSize[1]-squareSize):
                    left = (0,0,255)
                    if lefttime is None:
                        lefttime = time.perf_counter()
                        break
                if (screenSize[0] > center[0] > screenSize[0]-squareSize) and (screenSize[1]-squareSize < center[1] < screenSize[1]):
                    right = (0,0,255)
                    if righttime is None:
                        righttime = time.perf_counter()
                        break
        

        if left == (255,0,0):
            lefttime = None
        if right == (255,0,0):
            righttime = None
        

        if lefttime is not None:
            print(lefttime, time.perf_counter())
            if lefttime + selectionTime < time.perf_counter():
                break
        if righttime is not None:
            if righttime + selectionTime < time.perf_counter():
                exit()

        cv2.rectangle(screen, (0, screenSize[1]-squareSize), (squareSize, screenSize[1]), left, 20)
        cv2.rectangle(screen, (screenSize[0]-squareSize, screenSize[1]-squareSize), screenSize, right, 20)  
        
        CenteredText(screen, "Continue", (int(squareSize/2), int(screenSize[1]-(squareSize/2))), 1.7, (255, 0, 0), 4)
        CenteredText(screen, "Exit", (screenSize[0]-squareSize/2, int(screenSize[1]-(squareSize/2))), 1.7, (255, 0, 0), 4)
        #cv2.putText(screen, "Continue", (int(squareSize/2), int(screenSize[1]-(squareSize/2))), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 5)

        cv2.imshow('Webkamera', screen)
        cv2.waitKey(1)

# Kapcsolat bontása és ablakok bezárása
cap.release()
cv2.destroyAllWindows()