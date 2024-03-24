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

def DetectSquares(source, screen):
    blurred = cv2.GaussianBlur(source, (5, 5), 0)
    _, edges = cv2.threshold(blurred, 50, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(edges.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    test = np.zeros((screenSize[1], screenSize[0], 3), dtype = np.uint8)
    for contour in contours:
    # Approximate the contour to a polygon
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.05 * peri, True)

        
        cv2.drawContours(test, [approx], -1, (0, 0, 255), 2)
        
    
        # If the contour has 4 vertices, it's likely a square
        if len(approx) == 4 and peri < 300 and peri > 200:
            cv2.drawContours(screen, [approx], -1, (0, 255, 0), 10)

        if len(approx) == 3 and peri < 300 and peri > 200:
            cv2.drawContours(screen, [approx], -1, (0, 255, 0), 10)
    cv2.imshow("teszt", edges)
    cv2.imshow("teszt2", test)

def DisplayCircles(screen, circles):
    if circles is None:
        return
    for circle in circles[0, :]:
        center = (circle[0], circle[1])
        radius = circle[2]
        cv2.circle(screen, center, radius+5, (0, 0, 255), 3)


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


def Button(screen, circles, t, b, recThick, string, strSize, strThick):
    color = (255, 0, 0)
    if circles is not None:
        for circle in circles[0, :]:
            if (t[0] < circle[0] < b[0]) and (t[1] < circle[1] < b[1]):
                color = (0, 0, 255)

    CenteredText(screen, string, (t[0]+(b[0]-t[0])/2, t[0]+(b[0]-t[0])/2), strSize, color, strThick)
    cv2.rectangle(screen, t, b, color, recThick)

    if color == (255, 0, 0):
        return False
    else:
        return True

def Slider(screen, x, y1, y2, circles):
    cv2.line(screen, (x, y1), (x, y2), (255, 0, 0), 20)
    if circles is not None:
        for circle in circles[0, :]:
            if (x-100 < circle[0] < x+100) and (y1 < circle[1] < y2):
                cv2.line(screen, (x, y1), (x, circle[1]), (0, 255, 0), 20)
                cv2.circle(screen, (x, circle[1]), 30, (0, 255, 0), 30)
                return (circle[1]-y1)/(y2-y1)
    return 0

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

cv2.namedWindow("teszt", cv2.WINDOW_NORMAL)

#fulscreen
cv2.setWindowProperty("Webkamera", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cv2.imshow("Webkamera", megyek)
cv2.waitKey(1)


screen = megyek.copy()
while running:
    playerGuesses = []
    chosenLocations = []
    while False:


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

        cv2.imshow('Webkamera', screen)
        cv2.waitKey(1)
       
        #clear screen
        screen = megyekT.copy()
        screen = np.zeros((screenSize[1], screenSize[0], 3), dtype = np.uint8)

        DetectSquares(gray, screen)
        
        circles = DetectCircles(gray)

        DisplayCircles(screen, circles)

        value = Slider(screen, 500, 300, 1000, circles)

        CenteredText(screen, "Number of questions: "+str(int(round(value, 1)*10)), (600, 600), 4, (0, 0, 255), 5)

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
            closest = False

            if circles is not None:
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

            cv2.waitKey(1)

            if closest:
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

        #gray
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        #gray upscale
        gray = cv2.resize(gray, screenSize)

        circles = DetectCircles(gray)

        cv2.imshow('Webkamera', screen)
        cv2.waitKey(1)
        screen = megyekT.copy()
        #screen = np.zeros((screenSize[1], screenSize[0], 3), dtype = np.uint8)

        DisplayCircles(screen, circles)

        leftpressed = Button(screen, circles, (500, 500), (700, 700), 10, "Tesztgomb", 4, 3)
        rightpressed = Button(screen, circles, (100, 100), (400, 400), 10, "KÖZÉPREEEE", 3, 3)

        if leftpressed:
            if lefttime is None:
                lefttime = time.perf_counter()
        else:
            lefttime = None

        if rightpressed:
            if righttime is None:
                righttime = time.perf_counter()
        else:
            righttime = None


        if lefttime is not None:
            if lefttime + selectionTime < time.perf_counter():
                selecting = False
        if righttime is not None:
            if righttime + selectionTime < time.perf_counter():
                exit()

        """
        cv2.rectangle(screen, (0, screenSize[1]-squareSize), (squareSize, screenSize[1]), left, 20)
        cv2.rectangle(screen, (screenSize[0]-squareSize, screenSize[1]-squareSize), screenSize, right, 20)

        CenteredText(screen, "Continue", (int(squareSize/2), int(screenSize[1]-(squareSize/2))), 1.7, (255, 0, 0), 4)
        CenteredText(screen, "Exit", (screenSize[0]-squareSize/2, int(screenSize[1]-(squareSize/2))), 1.7, (255, 0, 0), 4)
        """


# Kapcsolat bontása és összes ablak bezárása
cap.release()
cv2.destroyAllWindows()
