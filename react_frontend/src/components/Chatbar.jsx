import React, { useState, useRef } from 'react';
import axios from 'axios';
import { FaMicrophone, FaStop } from 'react-icons/fa';
import { CgAttachment } from "react-icons/cg"
import OpenAI from 'openai';

const openaiApiKey = import.meta.env.VITE_OPENAI_API_KEY;
const openai = new OpenAI({ apiKey: openaiApiKey, dangerouslyAllowBrowser: true });

const Chatbar = ({ onSendMessage, onReportCreated }) => {
  const [input, setInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const audioChunks = useRef([]);
  const [modalIsOpen, setModalIsOpen] = useState(false);
  const [editText, setEditText] = useState('');
  const [modalCreateIsOpen,setModalCreateIsOpen]=useState(false); //another state is save_report
  const [editCreateText, setEditCreateText] = useState('');
  const [responseIntent, setResponseIntent] = useState('');
  const fileInputRef = useRef(null);

  const handleAttachmentClick = () => {
    fileInputRef.current.click();
  };

  const handleFileChange = async (event) => {
    const file = event.target.files[0];
    if (file) {
      const formData = new FormData();
      formData.append('file', file);
      onSendMessage({ sender: 'User', text: `File uploaded: ${file.name}` });
      try {
        const response = await axios.post('http://localhost:8000/process_file', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        
        console.log('OCR result:', response.data.text);
        //onSendMessage({ sender: 'Assistant', text: response.data.text });
        setModalCreateIsOpen(true)
        setEditCreateText(response.data.text)
        setResponseIntent('create')
      } catch (error) {
        console.error('Error uploading file:', error);
      }
    }
  };

  const handleSend = async () => {
    if (input.trim()) {
      const userMessage = { sender: 'User', text: input };
      onSendMessage(userMessage);
      handleSendMessageToBackend(input);
      setInput('');
    }
  };

  const handleRecording = async () => {
    if (isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const recorder = new MediaRecorder(stream);
        setMediaRecorder(recorder);

        recorder.ondataavailable = event => {
          audioChunks.current.push(event.data);
        };

        recorder.onstop = async () => {
          const audioBlob = new Blob(audioChunks.current, { type: 'audio/wav' });
          audioChunks.current = [];

          const transcription = await speechToText(audioBlob);
          setEditText(transcription);
          setModalIsOpen(true);
        };

        recorder.start();
        setIsRecording(true);
      } catch (error) {
        console.error('Error accessing microphone:', error);
      }
    }
  };

  const speechToText = async (audioBlob) => {
    const file = new File([audioBlob], 'audio.wav', { type: 'audio/wav' });
    try {
      const transcription = await openai.audio.transcriptions.create({
        file,
        model: 'whisper-1',
      });
      return transcription.text;
    } catch (error) {
      console.error('Error transcribing audio:', error);
      return 'Error transcribing audio';
    }
  };

  const handleSaveChanges = () => {
    const userMessage = { sender: 'User', text: editText };
    onSendMessage(userMessage);
    handleSendMessageToBackend(editText);
    setModalIsOpen(false);
  };

  const handleSaveCreateChanges=()=>{
    handleSendCreateMessageToBackend(editCreateText,responseIntent);
    setModalCreateIsOpen(false);
  }
  const parseResult = (resultString) => {
    const entries = resultString.split(' - ').map(entry => entry.trim());
    return (
      <ul>
        {entries.map((entry, index) => (
          <li key={index}>{entry}</li>
        ))}
      </ul>
    );
  };

  const handleSendMessageToBackend = async (message) => {
    try {
      const response = await axios.post('http://localhost:8000/process_request', { text: message });
      const result = response.data;
      let botReply;
      if (response.data.intent.toLowerCase() === 'create') {
        console.log('The intent is create')
        //Display result.create_output in a modal, where the content can be edited, and then the saved content can be given to the handleSendMessageToBackend function again, and this time the response that comes from the backend will be given to botReply in the text field and displayed on the screen
        setModalCreateIsOpen(true)
        setEditCreateText(result.create_output)
        setResponseIntent(result.intent.toLowerCase())
        // botReply = {
        //   sender: 'Assistant',
        //   text: `${result.create_output}`
        // };
      } else if (result.intent.toLowerCase() === 'read') {
        console.log(result.read_output)
        // const botReply = { sender: 'Assistant', text: result.read_output };
        const formattedOutput = parseResult(result.read_output);
        const botReply = { sender: 'Assistant', text: formattedOutput };
        onSendMessage(botReply);

      } else if (result.intent.toLowerCase() === 'update') {
        setModalCreateIsOpen(true)
        setEditCreateText(result.update_output)
        setResponseIntent(result.intent.toLowerCase())
      } else {
        botReply = { sender: 'Assistant', text: 'Undefined intent' };
      }
    } catch (error) {
      console.error('Error sending message to backend:', error);
    }
  };

  const handleSendCreateMessageToBackend=async(message,intent)=>{
    try{
      const response = await axios.post('http://localhost:8000/save_request', { 'text': message, 'intent': intent  });
      
      const botReply = {
        sender: 'Assistant',
        text: response.data.message,
      };

      onSendMessage(botReply);
      onReportCreated();
  }
  catch(error){
    console.error('Error sending message to backend:', error);
  }
  }

  return (
    <div className='text-white fixed bottom-0 w-full flex justify-center p-4 bg-gray-900'>
      <div className="flex items-center w-3/4 max-w-4xl ml-12">
      <button onClick={handleRecording} className={`ml-2 mr-3 p-3  text-white rounded-lg ${isRecording ? 'bg-red-700' : 'bg-green-700'}`}>
        {isRecording ? <FaStop /> : <FaMicrophone />}
      </button>
      <div className="relative w-1/2">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Speak in the microphone or type your query here..."
        className="w-full p-2 pr-10 text-black rounded-lg overflow-y-auto"
      />
      <button onClick={handleAttachmentClick}>
        <CgAttachment className="absolute right-3 top-1/2 transform -translate-y-1/2 text-black text-xl" />
      </button>
      <input
          type="file"
          ref={fileInputRef}
          className="hidden"
          onChange={handleFileChange}
        />
    </div>
      <button onClick={handleSend} className="ml-2 p-2 bg-blue-500 text-white rounded-lg">Send</button>
      </div>
      {modalIsOpen && (
        <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
          <div className="bg-white rounded-lg p-6 w-11/12 md:w-1/2 lg:w-1/3">
            <h2 className="text-2xl text-black mb-4">Edit Transcription</h2>
            <textarea
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              className="w-full p-2 h-40 text-black rounded-lg border border-gray-300"
            />
            <button
              onClick={handleSaveChanges}
              className="mt-4 mr-2 p-2 bg-green-500 text-white rounded-lg"
            >
              Save Changes
            </button>
            <button
              onClick={() => setModalIsOpen(false)}
              className="mt-4 p-2 bg-red-500 text-white rounded-lg"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
      {modalCreateIsOpen && (
        <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
          <div className="bg-white rounded-lg p-6 w-11/12 md:w-1/2 lg:w-1/3">
            <h2 className="text-2xl text-black mb-4">Edit Response</h2>
            <textarea
              value={editCreateText}
              onChange={(e) => setEditCreateText(e.target.value)}
              className="w-full p-2 h-40 text-black rounded-lg border border-gray-300"
            />
            <button
              onClick={handleSaveCreateChanges}
              className="mt-4 mr-2 p-2 bg-green-500 text-white rounded-lg"
            >
              Save Changes
            </button>
            <button
              onClick={() => setModalCreateIsOpen(false)}
              className="mt-4 p-2 bg-red-500 text-white rounded-lg"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default Chatbar;