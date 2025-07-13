import React, { useState, useRef } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, useNavigate, Link } from "react-router-dom";
import { 
  FileText, 
  Image as ImageIcon, 
  Calculator, 
  Upload, 
  Download, 
  Home as HomeIcon,
  Menu,
  X,
  Merge,
  Split,
  RotateCw,
  Crop,
  Palette,
  DollarSign,
  Smartphone
} from "lucide-react";
import { PDFDocument } from 'pdf-lib';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Home Component
const Home = () => {
  const navigate = useNavigate();
  
  const tools = [
    {
      id: 'pdf',
      title: 'PDF Tools',
      description: 'Merge, split, and manage PDF files',
      icon: FileText,
      color: 'bg-gradient-to-br from-red-500 to-red-600',
      features: ['Merge PDFs', 'Split PDFs', 'Fast Processing']
    },
    {
      id: 'image',
      title: 'Image Editor',
      description: 'Crop, rotate, and apply filters',
      icon: ImageIcon,
      color: 'bg-gradient-to-br from-blue-500 to-blue-600',
      features: ['Crop Images', 'Rotate & Flip', 'Apply Filters']
    },
    {
      id: 'converter',
      title: 'Unit Converter',
      description: 'Convert between IN/US/CA/AU units',
      icon: Calculator,
      color: 'bg-gradient-to-br from-green-500 to-green-600',
      features: ['Length & Weight', 'Temperature', 'Multiple Countries']
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Hero Section */}
      <div className="relative bg-gradient-to-r from-indigo-600 to-purple-600 text-white">
        <div 
          className="absolute inset-0 bg-cover bg-center opacity-20"
          style={{
            backgroundImage: 'url(https://images.unsplash.com/photo-1726056652641-de93ec003289)'
          }}
        ></div>
        <div className="relative px-4 py-16 text-center">
          <Smartphone className="w-16 h-16 mx-auto mb-4 text-white/90" />
          <h1 className="text-4xl font-bold mb-4">
            Mobile Tools Hub
          </h1>
          <p className="text-xl opacity-90 max-w-2xl mx-auto">
            Your all-in-one productivity suite for PDF management, image editing, and unit conversion
          </p>
        </div>
      </div>

      {/* Tools Grid */}
      <div className="px-4 py-8">
        <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">
          Choose Your Tool
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto">
          {tools.map((tool) => {
            const IconComponent = tool.icon;
            return (
              <div
                key={tool.id}
                onClick={() => navigate(`/${tool.id}`)}
                className="group cursor-pointer transform transition-all duration-300 hover:scale-105"
              >
                <div className="bg-white rounded-2xl shadow-lg overflow-hidden border border-gray-200">
                  <div className={`${tool.color} p-6 text-white`}>
                    <IconComponent className="w-12 h-12 mb-4" />
                    <h3 className="text-xl font-bold mb-2">{tool.title}</h3>
                    <p className="text-white/90 text-sm">{tool.description}</p>
                  </div>
                  
                  <div className="p-6">
                    <ul className="space-y-2">
                      {tool.features.map((feature, index) => (
                        <li key={index} className="flex items-center text-gray-600">
                          <div className="w-2 h-2 bg-gray-400 rounded-full mr-3"></div>
                          {feature}
                        </li>
                      ))}
                    </ul>
                    
                    <button className="w-full mt-4 bg-gray-800 text-white py-3 rounded-xl font-medium hover:bg-gray-700 transition-colors">
                      Open Tool
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Ad Banner */}
      <div className="fixed bottom-0 left-0 right-0 bg-gray-800 text-white p-4 text-center">
        <p className="text-sm">📱 Get Premium - Remove Ads & Unlock All Features</p>
      </div>
    </div>
  );
};

// PDF Tools Component
const PDFTools = () => {
  const [files, setFiles] = useState([]);
  const [mode, setMode] = useState('merge'); // 'merge' or 'split'
  const [isProcessing, setIsProcessing] = useState(false);
  const fileInputRef = useRef();

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    setFiles(selectedFiles);
  };

  const mergePDFs = async () => {
    if (files.length < 2) {
      alert('Please select at least 2 PDF files to merge');
      return;
    }

    setIsProcessing(true);
    try {
      const mergedPdf = await PDFDocument.create();
      
      for (const file of files) {
        const arrayBuffer = await file.arrayBuffer();
        const pdf = await PDFDocument.load(arrayBuffer);
        const copiedPages = await mergedPdf.copyPages(pdf, pdf.getPageIndices());
        copiedPages.forEach((page) => mergedPdf.addPage(page));
      }

      const pdfBytes = await mergedPdf.save();
      const blob = new Blob([pdfBytes], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = 'merged-document.pdf';
      a.click();
      
      URL.revokeObjectURL(url);
    } catch (error) {
      alert('Error merging PDFs: ' + error.message);
    }
    setIsProcessing(false);
  };

  const splitPDF = async () => {
    if (files.length !== 1) {
      alert('Please select exactly 1 PDF file to split');
      return;
    }

    setIsProcessing(true);
    try {
      const arrayBuffer = await files[0].arrayBuffer();
      const pdf = await PDFDocument.load(arrayBuffer);
      const pageCount = pdf.getPageCount();

      for (let i = 0; i < pageCount; i++) {
        const newPdf = await PDFDocument.create();
        const [copiedPage] = await newPdf.copyPages(pdf, [i]);
        newPdf.addPage(copiedPage);
        
        const pdfBytes = await newPdf.save();
        const blob = new Blob([pdfBytes], { type: 'application/pdf' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `page-${i + 1}.pdf`;
        a.click();
        
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      alert('Error splitting PDF: ' + error.message);
    }
    setIsProcessing(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center">
              <FileText className="w-8 h-8 text-red-500 mr-3" />
              <h1 className="text-2xl font-bold text-gray-800">PDF Tools</h1>
            </div>
            <Link to="/" className="text-gray-600 hover:text-gray-800">
              <HomeIcon className="w-6 h-6" />
            </Link>
          </div>

          {/* Mode Selector */}
          <div className="flex bg-gray-100 rounded-xl p-1 mb-6">
            <button
              onClick={() => setMode('merge')}
              className={`flex-1 flex items-center justify-center py-3 rounded-lg transition-colors ${
                mode === 'merge' ? 'bg-white shadow-sm text-red-600' : 'text-gray-600'
              }`}
            >
              <Merge className="w-5 h-5 mr-2" />
              Merge PDFs
            </button>
            <button
              onClick={() => setMode('split')}
              className={`flex-1 flex items-center justify-center py-3 rounded-lg transition-colors ${
                mode === 'split' ? 'bg-white shadow-sm text-red-600' : 'text-gray-600'
              }`}
            >
              <Split className="w-5 h-5 mr-2" />
              Split PDF
            </button>
          </div>

          {/* File Upload */}
          <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 mb-6 text-center">
            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 mb-4">
              {mode === 'merge' 
                ? 'Select 2 or more PDF files to merge' 
                : 'Select 1 PDF file to split into pages'
              }
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              multiple={mode === 'merge'}
              onChange={handleFileSelect}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current.click()}
              className="bg-red-500 text-white px-6 py-3 rounded-xl hover:bg-red-600 transition-colors"
            >
              Choose Files
            </button>
          </div>

          {/* Selected Files */}
          {files.length > 0 && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-800 mb-3">Selected Files:</h3>
              <div className="space-y-2">
                {files.map((file, index) => (
                  <div key={index} className="flex items-center bg-gray-50 p-3 rounded-lg">
                    <FileText className="w-5 h-5 text-red-500 mr-3" />
                    <span className="text-gray-700">{file.name}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Process Button */}
          <button
            onClick={mode === 'merge' ? mergePDFs : splitPDF}
            disabled={isProcessing || files.length === 0}
            className="w-full bg-red-500 text-white py-4 rounded-xl font-medium hover:bg-red-600 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {isProcessing ? 'Processing...' : (mode === 'merge' ? 'Merge PDFs' : 'Split PDF')}
          </button>
        </div>
      </div>

      {/* Ad Banner */}
      <div className="fixed bottom-0 left-0 right-0 bg-gray-800 text-white p-4 text-center">
        <p className="text-sm">📱 Get Premium - Remove Ads & Unlock All Features</p>
      </div>
    </div>
  );
};

// Image Editor Component
const ImageEditor = () => {
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [rotation, setRotation] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const fileInputRef = useRef();
  const canvasRef = useRef();

  const handleImageSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedImage(file);
      const reader = new FileReader();
      reader.onload = (e) => setImagePreview(e.target.result);
      reader.readAsDataURL(file);
    }
  };

  const rotateImage = () => {
    setRotation(prev => (prev + 90) % 360);
  };

  const applyFilter = (filterType) => {
    if (!selectedImage || !canvasRef.current) return;
    
    setIsProcessing(true);
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const img = new Image();
    
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      
      // Apply rotation
      ctx.save();
      ctx.translate(canvas.width / 2, canvas.height / 2);
      ctx.rotate((rotation * Math.PI) / 180);
      ctx.drawImage(img, -img.width / 2, -img.height / 2);
      ctx.restore();
      
      // Apply filter
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const data = imageData.data;
      
      switch (filterType) {
        case 'grayscale':
          for (let i = 0; i < data.length; i += 4) {
            const gray = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114;
            data[i] = data[i + 1] = data[i + 2] = gray;
          }
          break;
        case 'sepia':
          for (let i = 0; i < data.length; i += 4) {
            const r = data[i], g = data[i + 1], b = data[i + 2];
            data[i] = Math.min(255, r * 0.393 + g * 0.769 + b * 0.189);
            data[i + 1] = Math.min(255, r * 0.349 + g * 0.686 + b * 0.168);
            data[i + 2] = Math.min(255, r * 0.272 + g * 0.534 + b * 0.131);
          }
          break;
        case 'brightness':
          for (let i = 0; i < data.length; i += 4) {
            data[i] = Math.min(255, data[i] + 50);
            data[i + 1] = Math.min(255, data[i + 1] + 50);
            data[i + 2] = Math.min(255, data[i + 2] + 50);
          }
          break;
      }
      
      ctx.putImageData(imageData, 0, 0);
      setIsProcessing(false);
    };
    
    img.src = imagePreview;
  };

  const downloadImage = () => {
    if (!canvasRef.current) return;
    
    const canvas = canvasRef.current;
    const link = document.createElement('a');
    link.download = 'edited-image.png';
    link.href = canvas.toDataURL();
    link.click();
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center">
              <ImageIcon className="w-8 h-8 text-blue-500 mr-3" />
              <h1 className="text-2xl font-bold text-gray-800">Image Editor</h1>
            </div>
            <Link to="/" className="text-gray-600 hover:text-gray-800">
              <HomeIcon className="w-6 h-6" />
            </Link>
          </div>

          {/* File Upload */}
          {!selectedImage && (
            <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 mb-6 text-center">
              <ImageIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 mb-4">Select an image to edit</p>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleImageSelect}
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current.click()}
                className="bg-blue-500 text-white px-6 py-3 rounded-xl hover:bg-blue-600 transition-colors"
              >
                Choose Image
              </button>
            </div>
          )}

          {/* Image Editor */}
          {selectedImage && (
            <>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                {/* Preview */}
                <div className="space-y-4">
                  <h3 className="font-semibold text-gray-800">Preview</h3>
                  {imagePreview && (
                    <img
                      src={imagePreview}
                      alt="Preview"
                      className="w-full rounded-lg shadow-sm"
                      style={{ transform: `rotate(${rotation}deg)` }}
                    />
                  )}
                </div>

                {/* Controls */}
                <div className="space-y-4">
                  <h3 className="font-semibold text-gray-800">Tools</h3>
                  
                  <div className="space-y-3">
                    <button
                      onClick={rotateImage}
                      className="w-full flex items-center justify-center py-3 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
                    >
                      <RotateCw className="w-5 h-5 mr-2" />
                      Rotate 90°
                    </button>
                    
                    <button
                      onClick={() => applyFilter('grayscale')}
                      disabled={isProcessing}
                      className="w-full py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
                    >
                      Grayscale Filter
                    </button>
                    
                    <button
                      onClick={() => applyFilter('sepia')}
                      disabled={isProcessing}
                      className="w-full py-3 bg-yellow-100 text-yellow-700 rounded-lg hover:bg-yellow-200 transition-colors disabled:opacity-50"
                    >
                      Sepia Filter
                    </button>
                    
                    <button
                      onClick={() => applyFilter('brightness')}
                      disabled={isProcessing}
                      className="w-full py-3 bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200 transition-colors disabled:opacity-50"
                    >
                      Brighten
                    </button>
                    
                    <button
                      onClick={downloadImage}
                      className="w-full flex items-center justify-center py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                    >
                      <Download className="w-5 h-5 mr-2" />
                      Download
                    </button>
                  </div>
                </div>
              </div>

              <canvas ref={canvasRef} className="hidden" />
            </>
          )}
        </div>
      </div>

      {/* Ad Banner */}
      <div className="fixed bottom-0 left-0 right-0 bg-gray-800 text-white p-4 text-center">
        <p className="text-sm">📱 Get Premium - Remove Ads & Unlock All Features</p>
      </div>
    </div>
  );
};

// Unit Converter Component
const UnitConverter = () => {
  const [country, setCountry] = useState('US');
  const [category, setCategory] = useState('length');
  const [fromUnit, setFromUnit] = useState('');
  const [toUnit, setToUnit] = useState('');
  const [inputValue, setInputValue] = useState('');
  const [result, setResult] = useState('');

  const countries = {
    'US': 'United States',
    'IN': 'India', 
    'CA': 'Canada',
    'AU': 'Australia'
  };

  const units = {
    length: {
      US: { meter: 1, feet: 3.28084, inch: 39.3701, yard: 1.09361 },
      IN: { meter: 1, feet: 3.28084, inch: 39.3701, centimeter: 100 },
      CA: { meter: 1, feet: 3.28084, inch: 39.3701, kilometer: 0.001 },
      AU: { meter: 1, feet: 3.28084, inch: 39.3701, mile: 0.000621371 }
    },
    weight: {
      US: { kilogram: 1, pound: 2.20462, ounce: 35.274 },
      IN: { kilogram: 1, pound: 2.20462, gram: 1000 },
      CA: { kilogram: 1, pound: 2.20462, gram: 1000 },
      AU: { kilogram: 1, pound: 2.20462, gram: 1000 }
    },
    temperature: {
      US: { celsius: 1, fahrenheit: (c) => c * 9/5 + 32 },
      IN: { celsius: 1, fahrenheit: (c) => c * 9/5 + 32 },
      CA: { celsius: 1, fahrenheit: (c) => c * 9/5 + 32 },
      AU: { celsius: 1, fahrenheit: (c) => c * 9/5 + 32 }
    }
  };

  const convert = () => {
    if (!inputValue || !fromUnit || !toUnit) return;
    
    const value = parseFloat(inputValue);
    const unitSet = units[category][country];
    
    if (category === 'temperature') {
      if (fromUnit === 'fahrenheit' && toUnit === 'celsius') {
        setResult(((value - 32) * 5/9).toFixed(2));
      } else if (fromUnit === 'celsius' && toUnit === 'fahrenheit') {
        setResult((value * 9/5 + 32).toFixed(2));
      } else {
        setResult(value.toString());
      }
    } else {
      const baseValue = value / unitSet[fromUnit];
      const convertedValue = baseValue * unitSet[toUnit];
      setResult(convertedValue.toFixed(4));
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center">
              <Calculator className="w-8 h-8 text-green-500 mr-3" />
              <h1 className="text-2xl font-bold text-gray-800">Unit Converter</h1>
            </div>
            <Link to="/" className="text-gray-600 hover:text-gray-800">
              <HomeIcon className="w-6 h-6" />
            </Link>
          </div>

          {/* Country Selector */}
          <div className="mb-6">
            <h3 className="font-semibold text-gray-800 mb-3">Select Country</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {Object.entries(countries).map(([code, name]) => (
                <button
                  key={code}
                  onClick={() => setCountry(code)}
                  className={`p-3 rounded-lg text-center transition-colors ${
                    country === code 
                      ? 'bg-green-500 text-white' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  <div className="font-medium">{code}</div>
                  <div className="text-sm">{name}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Category Selector */}
          <div className="mb-6">
            <h3 className="font-semibold text-gray-800 mb-3">Category</h3>
            <div className="flex space-x-3">
              {Object.keys(units).map((cat) => (
                <button
                  key={cat}
                  onClick={() => setCategory(cat)}
                  className={`px-4 py-2 rounded-lg capitalize transition-colors ${
                    category === cat 
                      ? 'bg-green-500 text-white' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          {/* Converter */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div>
              <h3 className="font-semibold text-gray-800 mb-3">From</h3>
              <select
                value={fromUnit}
                onChange={(e) => setFromUnit(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              >
                <option value="">Select unit</option>
                {Object.keys(units[category][country]).map(unit => (
                  <option key={unit} value={unit}>{unit}</option>
                ))}
              </select>
              <input
                type="number"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Enter value"
                className="w-full p-3 border border-gray-300 rounded-lg mt-3 focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>

            <div>
              <h3 className="font-semibold text-gray-800 mb-3">To</h3>
              <select
                value={toUnit}
                onChange={(e) => setToUnit(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              >
                <option value="">Select unit</option>
                {Object.keys(units[category][country]).map(unit => (
                  <option key={unit} value={unit}>{unit}</option>
                ))}
              </select>
              <div className="w-full p-3 border border-gray-300 rounded-lg mt-3 bg-gray-50 text-gray-700 font-medium">
                {result || 'Result will appear here'}
              </div>
            </div>
          </div>

          <button
            onClick={convert}
            disabled={!inputValue || !fromUnit || !toUnit}
            className="w-full bg-green-500 text-white py-4 rounded-xl font-medium hover:bg-green-600 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            Convert
          </button>
        </div>
      </div>

      {/* Ad Banner */}
      <div className="fixed bottom-0 left-0 right-0 bg-gray-800 text-white p-4 text-center">
        <p className="text-sm">📱 Get Premium - Remove Ads & Unlock All Features</p>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/pdf" element={<PDFTools />} />
          <Route path="/image" element={<ImageEditor />} />
          <Route path="/converter" element={<UnitConverter />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;