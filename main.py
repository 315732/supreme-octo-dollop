import os  # Import the OS module to interact with the operating system
import cv2  # Import OpenCV for image processing and computer vision
from flask import Flask, Response, render_template, request, redirect, url_for, flash  # Import necessary Flask components
import requests  # Import the requests library to make HTTP requests

app = Flask(__name__)  # Initialize the Flask application
app.secret_key = 'your_secret_key'  # Set a secret key for session management and flashing messages

# Load the pre-trained Haar Cascade classifier for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Create a directory to save captured images if it doesn't exist
if not os.path.exists('static/captured_faces'):
    os.makedirs('static/captured_faces')  # Make the directory for captured faces

captured_image_path = 'static/captured_faces/captured_face.jpg'  # Path to save the captured face image

def generate_frames():
    # Open the video stream from a specified URL (e.g., IP camera)
    cap = cv2.VideoCapture("http://192.168.1.101:4747/video")

    while True:  # Continuous loop to read frames
        success, frame = cap.read()  # Read a frame from the camera
        if not success:
            break  # Exit the loop if no frame is captured
        
        # Convert the frame to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces in the grayscale frame
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

        # Draw rectangles around detected faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)  # Draw a rectangle around the face

            # Capture the detected face and save it
            face_img = frame[y:y + h, x:x + w]  # Extract the face from the frame
            cv2.imwrite(captured_image_path, face_img)  # Save the captured face image

            # Stop capturing after the first face is detected
            break

        # Encode the frame in JPEG format for streaming
        ret, buffer = cv2.imencode('.jpg', frame)  # Encode the frame to JPEG
        frame = buffer.tobytes()  # Convert to byte format

        # Yield the frame for streaming
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # Return the JPEG frame

@app.route('/')  # Define the route for the index page
def index():
    # Check if the captured image exists
    image_exists = os.path.exists(captured_image_path)  # Check if the captured face image file exists
    return render_template('index.html', image_exists=image_exists)  # Render the index template

@app.route('/video_feed')  # Define the route for video streaming
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')  # Stream the video frames

@app.route('/upload', methods=['POST'])  # Define the route for file upload
def upload_file():
    if request.method == 'POST':
        url = "https://probivapi.com/api/phone/pic/"  # API endpoint for uploading the captured image
        file_path = "static/captured_faces/captured_face.jpg"  # Path to the captured image
        api_key = "your_api_key_here"  # Placeholder for the API key

        with open(file_path, 'rb') as file:  # Open the captured image file in binary read mode
            files = {'file': file}  # Prepare the file for upload
            
            # Prepare the headers, including the API key for authentication
            headers = {
                'X-Auth': api_key  # Assuming the API uses Bearer token for authorization
            }
            
            # Send the POST request to the API with the image file and headers
            response = requests.post(url, files=files, headers=headers)
            
            # Check if the request was successful
            if response.status_code == 200:
                print("File uploaded successfully!")  # Log success message
                print("Response:", response.json())  # Print the JSON response from the API
                return redirect(url_for('index'))  # Redirect back to the index page
            else:
                flash('Failed to upload file.')  # Flash an error message
                return redirect(url_for('index'))  # Redirect back to the index page
    
    flash('Failed to upload file.')  # Flash an error message for unexpected POST requests
    return redirect(url_for('index'))  # Redirect back to the index page

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)  # Start the Flask application in debug mode
