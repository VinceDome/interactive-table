import cv2, time, math, random, os
import numpy as np
from PIL import ImageFont, ImageDraw, Image

yogaSize = (1366, 768)
screenSize = (1920, 1080)
clock_center = (962, 540)


testradius=20
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

class Button:
    timer = None
    isPressed = False
    def __init__(self, t, b, recThick, string, strSize, strThick) -> None:
        self.t = t
        self.b = b
        self.recThick = recThick
        self.string = string
        self.strSize = strSize
        self.strThick = strThick

    def update(self, screen, objects):
        
        color = (255, 0, 0)
        if objects is not None:
            for ob in objects:
                if (self.t[0] < ob[0] < self.b[0]) and (self.t[1] < ob[1] < self.b[1]):
                    color = (0, 0, 255)

        CenteredText(screen, self.string, (self.t[0]+(self.b[0]-self.t[0])/2, self.t[1]+(self.b[1]-self.t[1])/2), self.strSize, color, self.strThick)
        cv2.rectangle(screen, self.t, self.b, color, self.recThick)

        if color == (255, 0, 0):
            self.timer = None
        else:
            if self.timer is None:
                self.timer = time.perf_counter()
            elif self.timer + selectionTime < time.perf_counter():
                self.isPressed = True
                return
            
            ratio = (time.perf_counter()-self.timer)/selectionTime
            cv2.line(screen, self.t, (int(self.t[0]+(self.b[0]-self.t[0])*ratio), self.t[1]),(0, 255, 0), self.recThick)
        self.isPressed = False

class Slider:
    value = 0
    def __init__(self, t, b):
        self.t = t
        self.b = b
    def update(self, screen, objects):
        cv2.line(screen, self.t, self.b, (255, 0, 0), 20)
        if objects is not None:
            for ob in objects:
                if (self.t[0]-100 < ob[0] < self.t[0]+100) and (self.t[1] < ob[1] < self.b[1]):
                    cv2.line(screen, self.t, (self.t[0], int(ob[1])), (0, 255, 0), 20)
                    cv2.circle(screen, (self.t[0], int(ob[1])), 30, (0, 255, 0), 30)
                    self.value = (ob[1]-self.t[1])/(self.b[1]-self.t[1])
                    return
        self.value = 0

def DetectCircles(source):
    insideCircles = cv2.HoughCircles(
    source,                  # Bemeneti kép
    cv2.HOUGH_GRADIENT,    # Detekciós módszer
    dp=1,                  # Képméretarány
    minDist=100,            # Minimum távolság két kör között
    param1=50+50+50,             # Canny élek paraméter
    param2=30,             # A Hough transzformáció küszöbértéke
    minRadius=minR,          # Minimum kör sugara
    maxRadius=maxR          # Maximum kör sugara
    )


    # Ellenőrizze, hogy talált-e köröket
    if insideCircles is not None:
        # Körök koordinátáinak kinyerése
        return np.uint16(np.around(insideCircles))[0, :]

def DetectSquares(source, screen):
    #blurring
    blurred = cv2.GaussianBlur(source, (5, 5), 0)
    #thresholding
    _, edges = cv2.threshold(blurred, 50, 255, cv2.THRESH_BINARY)
    #drawing contours
    contours, _ = cv2.findContours(edges.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    test = np.zeros((screenSize[1], screenSize[0], 3), dtype = np.uint8)
    squares = []
    for contour in contours:
    # Approximate the contour to a polygon
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, (0.05-0.03) * peri, True)

        #drawing to test screen
        cv2.drawContours(test, contour, -1, (0, 255, 0), 2)
        cv2.drawContours(test, [approx], -1, (0, 0, 255), 2)
        
    
        # If the contour has 4 vertices, it's likely a square
        if len(approx) == 4 and peri < 300 and peri > 200:
            cv2.drawContours(screen, [approx], -1, (255, 0, 0), 10)
            #calculating centre based on average vertice location
            x=0
            y=0
            for i in approx:
                cv2.circle(screen, i[0], 5, (0, 0, 255), 5)
                x+=i[0][0]
                y+=i[0][1]
            squares.append((x/4, y/4))

        if len(approx) == 3 and peri < 500 and peri > 0:
            cv2.drawContours(screen, [approx], -1, (255, 0, 0), 10)

    #displaying test screens
    cv2.imshow("teszt", edges)
    cv2.imshow("teszt2", test)

    return squares

def DisplayCircles(screen, circles):
    if circles is None:
        return
    for circle in circles:
        
        center = (circle[0], circle[1])
        radius = circle[2]
        cv2.circle(screen, center, radius+5, (0, 0, 255), 3)
        #cv2.circle(screen, center, testradius, (255, 0, 0), testwidth)

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

def RandomHour():
    num = random.randint(0, 288)
    ora = math.floor(num/12)
    perc = (num%12)*5
    nagymutato = ((num%12)/12)*360
    kismutato = (((num/12)%12)/12)*360
    return kismutato, nagymutato, f"{ora}:{perc}"
    

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
megyek = cv2.imread("vakterkep_edit.png")
megyek = cv2.resize(megyek, screenSize)

ora = cv2.imread("cropped-ora.png")
ora = cv2.resize(ora, screenSize)
#ablak kreálás
cv2.namedWindow("main", cv2.WINDOW_NORMAL)

#az ablaknak a mozgatása a projektor másodlagos képernyőjére
cv2.moveWindow("main", yogaSize[0], 0)

cv2.namedWindow("teszt", cv2.WINDOW_NORMAL)
cv2.namedWindow("teszt2", cv2.WINDOW_NORMAL)
cv2.moveWindow("teszt2", 0, 500)

#fulscreen
cv2.setWindowProperty("main", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cv2.imshow("main", megyek)
cv2.waitKey(1)

blank = np.zeros((screenSize[1], screenSize[0], 3), dtype = np.uint8)
screen = blank.copy()



while running:
    playerGuesses = []
    chosenLocations = []
    gameButton = Button((500, 200), (1920-500, 900), 10, "Game", 4, 3)
    clockButton = Button((500, 600), (1920-500, 900), 10, "Clock", 4, 3)
    showButton = Button((1920-200, 300), (1920-100, 500), 10, "Showcase", 4, 3)
    
    
    while not gameButton.isPressed and not showButton.isPressed and not clockButton.isPressed:

        ret, frame = cap.read()
        #check ha hiba
        if not ret:
            print("Hiba a kép beolvasásakor")
            break

        #gray
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        #gray upscale
        gray = cv2.resize(gray, screenSize)

        cv2.imshow('main', screen)
        cv2.waitKey(1)
        
        #clear screen
        screen = blank.copy()
        #screen = np.zeros((screenSize[1], screenSize[0], 3), dtype = np.uint8)

        squares = DetectSquares(gray, screen)
        
        circles = DetectCircles(gray)

        showButton.update(screen, circles)
        gameButton.update(screen, circles)
        clockButton.update(screen, circles)

        DisplayCircles(screen, circles)

    if gameButton.isPressed:
        game = True
        while game:
            #kérdések kisorsolása egy listába
            allLocationsR = allLocations[:]
            chosenLocations = []
            for i in range(questions):
                loc = random.choice(allLocationsR)
                chosenLocations.append(Location(loc))
                allLocationsR.remove(loc)

            for location in chosenLocations:

                #létrehozok egy alaphátteret, így nem kell minden kamerafeldolgozásnál kiírni az adott helyszín nevét
                megyekT = megyek.copy()
                CenteredText(megyekT, location.name, (screenSize[0]/2, 100), 5, (255, 0, 0), 20)
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

                    #timer
                    cv2.putText(screen, str(round((st+guessTime-time.perf_counter()))), (100, 300), cv2.FONT_HERSHEY_SIMPLEX, 5, (255, 0, 0), 20)

                    circles = DetectCircles(gray)
                
                    if circles is not None:
                        #összes körön végigmenni
                        for circle in circles:
                            center = (circle[0], circle[1])
                            radius = circle[2]

                            #utolsó fél másodperc, az összes távolságot elmentem, amiből kiválasztom a legközelebbit
                            if time.perf_counter() > st + guessTime - 0.5:
                                dist = int(math.dist(location.coords, center))

                                dists.append(Guess(dist, center, radius))

                            cv2.circle(screen, center, radius+5, (0, 0, 255), 3)
                            #cv2.circle(megyek, center, testradius, (255, 0, 0), testwidth)



                    # Kijelzés a képernyőn

                    #képfrissítés
                    cv2.imshow('main', screen)

                    cv2.waitKey(1)

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

                    cv2.putText(screen, str(round((wt+displayTime-time.perf_counter()))), (300, 300), cv2.FONT_HERSHEY_SIMPLEX, 5, (255, 0, 0), 20)


                    cv2.imshow('main', screen)
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

            
            CenteredText(screen, f"Total distance: {totalDistance}", (screenSize[0]/2, 950), 3, (255, 0, 0), 10)
            megyekT = screen.copy()
            cv2.imshow('main', screen)
            cv2.waitKey(1)

            selecting = True

            contButton = Button((500, 600), (1920-500, 900), 15, "Continue", 4, 3)
            exitButton = Button((500, 200), (1920-500, 500), 15, "Exit", 4, 3)

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

                cv2.imshow('main', screen)
                cv2.waitKey(1)

                screen = megyekT.copy()
                #screen = np.zeros((screenSize[1], screenSize[0], 3), dtype = np.uint8)

                DisplayCircles(screen, circles)

                contButton.update(screen, circles)
                exitButton.update(screen, circles)

                if contButton.isPressed:
                    selecting = False
                if exitButton.isPressed:
                    game = False
                    selecting = False
    
    elif showButton.isPressed:
        showcasing = True
        menuButton = Button((1400, 500), (1800, 900), 15, "Menu", 4, 3)
        showSlider = Slider((500, 300), (500, 1000))
        while showcasing:
            ret, frame = cap.read()
            #check ha hiba
            if not ret:
                print("Hiba a kép beolvasásakor")
                break

            #gray
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            #gray upscale
            gray = cv2.resize(gray, screenSize)

            cv2.imshow('main', screen)
            cv2.waitKey(1)
            
            #clear screen
            screen = megyek.copy()
            #screen = np.zeros((screenSize[1], screenSize[0], 3), dtype = np.uint8)

            circles = DetectCircles(gray)

            squares = DetectSquares(gray, screen)

            DisplayCircles(screen, circles)


            showSlider.update(screen, squares)
            CenteredText(screen, str(round(showSlider.value, 2)), (900, 750), 5, (255, 0, 0), 4)
            menuButton.update(screen, circles)
            if menuButton.isPressed:
                showcasing = False

    elif clockButton.isPressed:
        clock = True
        while clock:
            playerGuesses = []
            chosen_times = []
            for i in range(questions):
                chosen_times.append(list(RandomHour()))

            
            
            
            
            for toguess in chosen_times:
                #alapháttér létrehozása
                oraT = ora.copy()
                CenteredText(oraT, toguess[2], (screenSize[0]/2, 100), 5, (255, 0, 0), 20)

                kisAngles = []
                nagyAngles = []
                st = time.perf_counter()
                #while guessing
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

                    cv2.imshow('main', screen)
                    cv2.waitKey(1)

                    screen = oraT.copy()

                    #timer
                    cv2.putText(screen, str(round((st+guessTime-time.perf_counter()))), (100, 300), cv2.FONT_HERSHEY_SIMPLEX, 5, (255, 0, 0), 20)

                    circles = DetectCircles(gray)

                    if circles is not None:
                        #összes körön végigmenni
                        for circle in circles:
                            center = (circle[0], circle[1])
                            radius = circle[2]
                            distToCenter = math.dist(center, clock_center)
                            lineWidth = 10
                            if distToCenter < 300:
                                color = (0, 0, 255)
                            else:
                                color = (255, 0, 0)
                                lineWidth += 7

                            #utolsó fél másodperc, az összes távolságot elmentem, amiből kiválasztom a legközelebbit
                            if time.perf_counter() > st + guessTime - 0.5:
                                
                                dx, dy = clock_center[0]-center[0], clock_center[1]-center[1]
                                angle = math.degrees(math.atan2(dy, dx))
                                angle -= 90

                                if angle < 0:
                                    angle += 360
                                
                                if distToCenter < 300:
                                     
                                    distToAngle = abs(toguess[0]-angle)
                                    kisAngles.append([angle, distToAngle, center, radius])
                                else:
                                    distToAngle = abs(toguess[1]-angle)
                                    nagyAngles.append([angle, distToAngle, center, radius])
                                

                            cv2.circle(screen, center, radius+5, color, 3)
                            #cv2.circle(screen, clock_center, testradius, (255, 0, 0), testwidth)
                            cv2.line(screen, clock_center, center, color, lineWidth)
                            
                if not kisAngles or not nagyAngles:
                    kisBest, nagyBest = False, False
                else:
                    #selecting smallest
                    kisBest = min(kisAngles, key=lambda x: x[1])
                    nagyBest = min(nagyAngles, key=lambda x: x[1])

                    #subtracting the tolerance
                    kisBest[1] = max(kisBest[1]-5, 0)
                    nagyBest[1] = max(nagyBest[1]-5, 0)

                    print(kisBest, nagyBest)


                playerGuesses.append([kisBest, nagyBest])

                #displaying results
                wt = time.perf_counter()
                while time.perf_counter() < wt + displayTime:
                    screen = oraT.copy()
                    #if this guess has any value
                    
                    if kisBest:
                        if kisBest[0]:
                        #draw in the guesses the player made
                            cv2.line(screen, clock_center, kisBest[2], (0, 0, 255), 10)
                            cv2.line(screen, clock_center, nagyBest[2], (255, 0, 0), 10)

                            
                            #draw in the correct orientation of the clock
                            endpoint = [int(200*(math.cos((toguess[0]-90)*(math.pi/180)))+clock_center[0]), int(200*(math.sin((toguess[0]-90)*(math.pi/180)))+clock_center[1])]
                            cv2.line(screen, clock_center, endpoint, (0, 255, 0), 10)

                            endpoint = [int(450*(math.cos((toguess[1]-90)*(math.pi/180)))+clock_center[0]), int(450*(math.sin((toguess[1]-90)*(math.pi/180)))+clock_center[1])]
                            cv2.line(screen, clock_center, endpoint, (0, 255, 0), 10)

                            

                            CenteredText(screen, f"Kismutato elteres: {round(kisBest[1], 1)}", (screenSize[0]/2, 750), 3, (255, 0, 0), 10)
                            CenteredText(screen, f"Nagymutato elteres: {round(nagyBest[1], 1)}", (screenSize[0]/2, 950), 3, (255, 0, 0), 10)
                    else:
                        CenteredText(screen, "Nincs tipp", (screenSize[0]/2, 950), 3, (255, 0, 0), 10)

                    cv2.putText(screen, str(round((wt+displayTime-time.perf_counter()))), (300, 300), cv2.FONT_HERSHEY_SIMPLEX, 5, (255, 0, 0), 20)


                    cv2.imshow('main', screen)
                    cv2.waitKey(1)

                    time.sleep(0.5)

            nagyDeviance = 0
            kisDeviance = 0
            for i in playerGuesses:
                kisDeviance += i[0][1]
                nagyDeviance += i[1][1]
            
            oraT = ora.copy()

            CenteredText(oraT, f"Kitmutato elteres: {round(kisDeviance, 1)}", (900, 200), 3, (255, 0, 0), 11)
            CenteredText(oraT, f"Nagymutato elteres: {round(nagyDeviance, 1)}", (900, 400), 3, (255, 0, 0), 11)
            

            selecting = True
    
            contButton = Button((200, 500), (900, 800), 15, "Continue", 4, 11)
            exitButton = Button((1020, 500), (1620, 800), 15, "Exit", 4, 11)

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

                cv2.imshow('main', screen)
                cv2.waitKey(1)

                screen = oraT.copy()

                DisplayCircles(screen, circles)

                contButton.update(screen, circles)
                exitButton.update(screen, circles)

                if contButton.isPressed:
                    selecting = False
                if exitButton.isPressed:
                    clock = False
                    selecting = False

cap.release()
cv2.destroyAllWindows()
