import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement } from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';
import jsPDF from 'jspdf';
import 'jspdf-autotable';
import { v4 as uuidv4 } from 'uuid';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement);

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Advanced validation functions (frontend)
const validateAadhaar = (aadhaar) => {
  if (!aadhaar || aadhaar.length !== 12 || !/^\d{12}$/.test(aadhaar)) {
    return false;
  }
  if (new Set(aadhaar).size === 1) return false;
  return true;
};

const validatePAN = (pan) => {
  const pattern = /^[A-Z]{5}[0-9]{4}[A-Z]{1}$/;
  return pattern.test(pan.toUpperCase());
};

const validateMobile = (mobile) => {
  const cleaned = mobile.replace(/\D/g, '');
  return (cleaned.length === 10 && /^[6-9]/.test(cleaned)) ||
         (cleaned.length === 12 && cleaned.startsWith('91') && /^[6-9]/.test(cleaned[2]));
};

const validateEmail = (email) => {
  const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return pattern.test(email);
};

function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [tours, setTours] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [dashboardStats, setDashboardStats] = useState({});
  const [loading, setLoading] = useState(false);

  // Customer form states
  const [customerForm, setCustomerForm] = useState({
    tour_id: '',
    first_name: '',
    last_name: '',
    date_of_birth: '',
    gender: '',
    email: '',
    mobile: '',
    address: '',
    city: '',
    state: '',
    pincode: '',
    aadhaar_number: '',
    pan_number: '',
    emergency_contact_name: '',
    emergency_contact_number: '',
    special_requirements: '',
    payment_method: ''
  });

  const [formErrors, setFormErrors] = useState({});
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [reviewData, setReviewData] = useState({});

  // Tour form states
  const [tourForm, setTourForm] = useState({
    name: '',
    destination: '',
    start_date: '',
    end_date: '',
    price: '',
    transport_mode: '',
    description: '',
    max_capacity: 50,
    image_url: ''
  });

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [toursRes, customersRes, expensesRes, statsRes] = await Promise.all([
        axios.get(`${API}/tours`),
        axios.get(`${API}/customers`),
        axios.get(`${API}/expenses`),
        axios.get(`${API}/dashboard/stats`)
      ]);
      
      setTours(toursRes.data);
      setCustomers(customersRes.data);
      setExpenses(expensesRes.data);
      setDashboardStats(statsRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
    }
    setLoading(false);
  };

  const validateCustomerForm = async () => {
    const errors = {};
    
    // Required field validation
    const requiredFields = [
      'tour_id', 'first_name', 'last_name', 'date_of_birth', 'gender',
      'email', 'mobile', 'address', 'city', 'state', 'pincode', 
      'aadhaar_number', 'emergency_contact_name', 'emergency_contact_number'
    ];
    
    requiredFields.forEach(field => {
      if (!customerForm[field]) {
        errors[field] = 'This field is required';
      }
    });

    // Advanced validation
    if (customerForm.aadhaar_number && !validateAadhaar(customerForm.aadhaar_number)) {
      errors.aadhaar_number = 'Invalid Aadhaar number format';
    }

    if (customerForm.pan_number && !validatePAN(customerForm.pan_number)) {
      errors.pan_number = 'Invalid PAN number format (e.g., ABCDE1234F)';
    }

    if (customerForm.email && !validateEmail(customerForm.email)) {
      errors.email = 'Invalid email format';
    }

    if (customerForm.mobile && !validateMobile(customerForm.mobile)) {
      errors.mobile = 'Invalid mobile number format';
    }

    if (customerForm.emergency_contact_number && !validateMobile(customerForm.emergency_contact_number)) {
      errors.emergency_contact_number = 'Invalid emergency contact number format';
    }

    // Date validation
    if (customerForm.date_of_birth) {
      const birthDate = new Date(customerForm.date_of_birth);
      const today = new Date();
      const age = today.getFullYear() - birthDate.getFullYear();
      if (age < 18 || age > 100) {
        errors.date_of_birth = 'Age must be between 18 and 100 years';
      }
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleCustomerSubmit = async (e) => {
    e.preventDefault();
    const isValid = await validateCustomerForm();
    
    if (isValid) {
      // Show review modal
      const selectedTour = tours.find(t => t.tour_id === customerForm.tour_id);
      setReviewData({
        ...customerForm,
        tour_name: selectedTour?.name || 'Unknown Tour'
      });
      setShowReviewModal(true);
    }
  };

  const confirmCustomerSubmission = async () => {
    try {
      setLoading(true);
      await axios.post(`${API}/customers`, customerForm);
      alert('Customer registered successfully!');
      setShowReviewModal(false);
      setCustomerForm({
        tour_id: '', first_name: '', last_name: '', date_of_birth: '',
        gender: '', email: '', mobile: '', address: '', city: '',
        state: '', pincode: '', aadhaar_number: '', pan_number: '',
        emergency_contact_name: '', emergency_contact_number: '',
        special_requirements: '', payment_method: ''
      });
      loadDashboardData();
    } catch (error) {
      alert('Error registering customer: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
  };

  const handleTourSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      await axios.post(`${API}/tours`, tourForm);
      alert('Tour created successfully!');
      setTourForm({
        name: '', destination: '', start_date: '', end_date: '',
        price: '', transport_mode: '', description: '', max_capacity: 50, image_url: ''
      });
      loadDashboardData();
    } catch (error) {
      alert('Error creating tour: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
  };

  const exportToPDF = () => {
    const doc = new jsPDF();
    doc.text('निसर्ग भ्रमंती - Customer Report', 20, 20);
    
    const tableData = customers.map(customer => [
      customer.first_name + ' ' + customer.last_name,
      customer.email,
      customer.mobile,
      tours.find(t => t.tour_id === customer.tour_id)?.name || 'Unknown',
      customer.payment_status
    ]);
    
    doc.autoTable({
      head: [['Name', 'Email', 'Mobile', 'Tour', 'Payment Status']],
      body: tableData,
      startY: 30
    });
    
    doc.save('customers-report.pdf');
  };

  const exportToCSV = () => {
    const headers = ['Name', 'Email', 'Mobile', 'Tour', 'Payment Status', 'Date of Birth'];
    const csvData = customers.map(customer => [
      customer.first_name + ' ' + customer.last_name,
      customer.email,
      customer.mobile,
      tours.find(t => t.tour_id === customer.tour_id)?.name || 'Unknown',
      customer.payment_status,
      customer.date_of_birth
    ]);
    
    const csvContent = [headers, ...csvData]
      .map(row => row.map(field => `"${field}"`).join(','))
      .join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'customers-export.csv';
    a.click();
  };

  const chartData = {
    labels: dashboardStats.tour_stats?.map(stat => stat.tour_info?.name) || [],
    datasets: [{
      label: 'Revenue by Tour',
      data: dashboardStats.tour_stats?.map(stat => stat.revenue) || [],
      backgroundColor: [
        'rgba(54, 162, 235, 0.6)',
        'rgba(255, 99, 132, 0.6)',
        'rgba(255, 206, 86, 0.6)',
        'rgba(75, 192, 192, 0.6)'
      ],
      borderColor: [
        'rgba(54, 162, 235, 1)',
        'rgba(255, 99, 132, 1)',
        'rgba(255, 206, 86, 1)',
        'rgba(75, 192, 192, 1)'
      ],
      borderWidth: 2
    }]
  };

  const doughnutData = {
    labels: ['Revenue', 'Expenses'],
    datasets: [{
      data: [dashboardStats.total_revenue || 0, dashboardStats.total_expenses || 0],
      backgroundColor: ['#10B981', '#EF4444'],
      borderWidth: 2
    }]
  };

  const renderDashboard = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-xl shadow-lg border-l-4 border-blue-500">
          <h3 className="text-lg font-semibold text-gray-700">Total Tours</h3>
          <p className="text-3xl font-bold text-blue-600">{dashboardStats.total_tours || 0}</p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-lg border-l-4 border-green-500">
          <h3 className="text-lg font-semibold text-gray-700">Total Customers</h3>
          <p className="text-3xl font-bold text-green-600">{dashboardStats.total_customers || 0}</p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-lg border-l-4 border-purple-500">
          <h3 className="text-lg font-semibold text-gray-700">Total Revenue</h3>
          <p className="text-3xl font-bold text-purple-600">₹{(dashboardStats.total_revenue || 0).toLocaleString()}</p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-lg border-l-4 border-red-500">
          <h3 className="text-lg font-semibold text-gray-700">Total Profit</h3>
          <p className="text-3xl font-bold text-red-600">₹{(dashboardStats.profit || 0).toLocaleString()}</p>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-xl shadow-lg">
          <h3 className="text-xl font-semibold mb-4">Revenue by Tour</h3>
          {dashboardStats.tour_stats?.length > 0 ? (
            <Bar data={chartData} options={{ responsive: true }} />
          ) : (
            <p className="text-gray-500">No data available</p>
          )}
        </div>
        <div className="bg-white p-6 rounded-xl shadow-lg">
          <h3 className="text-xl font-semibold mb-4">Revenue vs Expenses</h3>
          {(dashboardStats.total_revenue || 0) > 0 ? (
            <Doughnut data={doughnutData} options={{ responsive: true }} />
          ) : (
            <p className="text-gray-500">No data available</p>
          )}
        </div>
      </div>
    </div>
  );

  const renderCustomerForm = () => (
    <div className="bg-white p-8 rounded-xl shadow-lg">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">Customer Registration</h2>
      <form onSubmit={handleCustomerSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Tour Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Select Tour *</label>
            <select
              value={customerForm.tour_id}
              onChange={(e) => setCustomerForm({...customerForm, tour_id: e.target.value})}
              className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 ${formErrors.tour_id ? 'border-red-500' : 'border-gray-300'}`}
              required
            >
              <option value="">Choose a tour</option>
              {tours.map(tour => (
                <option key={tour.tour_id} value={tour.tour_id}>
                  {tour.name} - ₹{tour.price.toLocaleString()}
                </option>
              ))}
            </select>
            {formErrors.tour_id && <p className="text-red-500 text-sm mt-1">{formErrors.tour_id}</p>}
          </div>

          {/* Personal Information */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">First Name *</label>
            <input
              type="text"
              value={customerForm.first_name}
              onChange={(e) => setCustomerForm({...customerForm, first_name: e.target.value})}
              className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 ${formErrors.first_name ? 'border-red-500' : 'border-gray-300'}`}
              required
            />
            {formErrors.first_name && <p className="text-red-500 text-sm mt-1">{formErrors.first_name}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Last Name *</label>
            <input
              type="text"
              value={customerForm.last_name}
              onChange={(e) => setCustomerForm({...customerForm, last_name: e.target.value})}
              className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 ${formErrors.last_name ? 'border-red-500' : 'border-gray-300'}`}
              required
            />
            {formErrors.last_name && <p className="text-red-500 text-sm mt-1">{formErrors.last_name}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Date of Birth *</label>
            <input
              type="date"
              value={customerForm.date_of_birth}
              onChange={(e) => setCustomerForm({...customerForm, date_of_birth: e.target.value})}
              className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 ${formErrors.date_of_birth ? 'border-red-500' : 'border-gray-300'}`}
              required
            />
            {formErrors.date_of_birth && <p className="text-red-500 text-sm mt-1">{formErrors.date_of_birth}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Gender *</label>
            <select
              value={customerForm.gender}
              onChange={(e) => setCustomerForm({...customerForm, gender: e.target.value})}
              className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 ${formErrors.gender ? 'border-red-500' : 'border-gray-300'}`}
              required
            >
              <option value="">Select Gender</option>
              <option value="Male">Male</option>
              <option value="Female">Female</option>
              <option value="Other">Other</option>
            </select>
            {formErrors.gender && <p className="text-red-500 text-sm mt-1">{formErrors.gender}</p>}
          </div>

          {/* Contact Information */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Email *</label>
            <input
              type="email"
              value={customerForm.email}
              onChange={(e) => setCustomerForm({...customerForm, email: e.target.value})}
              className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 ${formErrors.email ? 'border-red-500' : 'border-gray-300'}`}
              required
            />
            {formErrors.email && <p className="text-red-500 text-sm mt-1">{formErrors.email}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Mobile Number *</label>
            <input
              type="tel"
              value={customerForm.mobile}
              onChange={(e) => setCustomerForm({...customerForm, mobile: e.target.value})}
              className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 ${formErrors.mobile ? 'border-red-500' : 'border-gray-300'}`}
              placeholder="10-digit mobile number"
              required
            />
            {formErrors.mobile && <p className="text-red-500 text-sm mt-1">{formErrors.mobile}</p>}
          </div>

          {/* Address */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">Address *</label>
            <textarea
              value={customerForm.address}
              onChange={(e) => setCustomerForm({...customerForm, address: e.target.value})}
              className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 ${formErrors.address ? 'border-red-500' : 'border-gray-300'}`}
              rows="3"
              required
            />
            {formErrors.address && <p className="text-red-500 text-sm mt-1">{formErrors.address}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">City *</label>
            <input
              type="text"
              value={customerForm.city}
              onChange={(e) => setCustomerForm({...customerForm, city: e.target.value})}
              className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 ${formErrors.city ? 'border-red-500' : 'border-gray-300'}`}
              required
            />
            {formErrors.city && <p className="text-red-500 text-sm mt-1">{formErrors.city}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">State *</label>
            <input
              type="text"
              value={customerForm.state}
              onChange={(e) => setCustomerForm({...customerForm, state: e.target.value})}
              className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 ${formErrors.state ? 'border-red-500' : 'border-gray-300'}`}
              required
            />
            {formErrors.state && <p className="text-red-500 text-sm mt-1">{formErrors.state}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Pincode *</label>
            <input
              type="text"
              value={customerForm.pincode}
              onChange={(e) => setCustomerForm({...customerForm, pincode: e.target.value})}
              className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 ${formErrors.pincode ? 'border-red-500' : 'border-gray-300'}`}
              pattern="[0-9]{6}"
              required
            />
            {formErrors.pincode && <p className="text-red-500 text-sm mt-1">{formErrors.pincode}</p>}
          </div>

          {/* Identity Documents */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Aadhaar Number *</label>
            <input
              type="text"
              value={customerForm.aadhaar_number}
              onChange={(e) => setCustomerForm({...customerForm, aadhaar_number: e.target.value})}
              className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 ${formErrors.aadhaar_number ? 'border-red-500' : 'border-gray-300'}`}
              placeholder="12-digit Aadhaar number"
              maxLength="12"
              required
            />
            {formErrors.aadhaar_number && <p className="text-red-500 text-sm mt-1">{formErrors.aadhaar_number}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">PAN Number (Optional)</label>
            <input
              type="text"
              value={customerForm.pan_number}
              onChange={(e) => setCustomerForm({...customerForm, pan_number: e.target.value.toUpperCase()})}
              className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 ${formErrors.pan_number ? 'border-red-500' : 'border-gray-300'}`}
              placeholder="ABCDE1234F"
              maxLength="10"
            />
            {formErrors.pan_number && <p className="text-red-500 text-sm mt-1">{formErrors.pan_number}</p>}
          </div>

          {/* Emergency Contact */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Emergency Contact Name *</label>
            <input
              type="text"
              value={customerForm.emergency_contact_name}
              onChange={(e) => setCustomerForm({...customerForm, emergency_contact_name: e.target.value})}
              className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 ${formErrors.emergency_contact_name ? 'border-red-500' : 'border-gray-300'}`}
              required
            />
            {formErrors.emergency_contact_name && <p className="text-red-500 text-sm mt-1">{formErrors.emergency_contact_name}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Emergency Contact Number *</label>
            <input
              type="tel"
              value={customerForm.emergency_contact_number}
              onChange={(e) => setCustomerForm({...customerForm, emergency_contact_number: e.target.value})}
              className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 ${formErrors.emergency_contact_number ? 'border-red-500' : 'border-gray-300'}`}
              required
            />
            {formErrors.emergency_contact_number && <p className="text-red-500 text-sm mt-1">{formErrors.emergency_contact_number}</p>}
          </div>

          {/* Additional Fields */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">Special Requirements (Optional)</label>
            <textarea
              value={customerForm.special_requirements}
              onChange={(e) => setCustomerForm({...customerForm, special_requirements: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              rows="2"
              placeholder="Any dietary restrictions, medical conditions, or special requests..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Payment Method (Optional)</label>
            <select
              value={customerForm.payment_method}
              onChange={(e) => setCustomerForm({...customerForm, payment_method: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select Payment Method</option>
              <option value="Cash">Cash</option>
              <option value="Card">Debit/Credit Card</option>
              <option value="UPI">UPI</option>
              <option value="Net Banking">Net Banking</option>
              <option value="Cheque">Cheque</option>
            </select>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {loading ? 'Processing...' : 'Review Details'}
          </button>
        </div>
      </form>
    </div>
  );

  const renderReviewModal = () => (
    showReviewModal && (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white p-8 rounded-xl shadow-xl max-w-4xl w-full mx-4 max-h-screen overflow-y-auto">
          <h2 className="text-2xl font-bold mb-6 text-gray-800">Review Customer Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            <div><strong>Tour:</strong> {reviewData.tour_name}</div>
            <div><strong>Name:</strong> {reviewData.first_name} {reviewData.last_name}</div>
            <div><strong>Date of Birth:</strong> {reviewData.date_of_birth}</div>
            <div><strong>Gender:</strong> {reviewData.gender}</div>
            <div><strong>Email:</strong> {reviewData.email}</div>
            <div><strong>Mobile:</strong> {reviewData.mobile}</div>
            <div className="md:col-span-2"><strong>Address:</strong> {reviewData.address}</div>
            <div><strong>City:</strong> {reviewData.city}</div>
            <div><strong>State:</strong> {reviewData.state}</div>
            <div><strong>Pincode:</strong> {reviewData.pincode}</div>
            <div><strong>Aadhaar:</strong> {reviewData.aadhaar_number}</div>
            <div><strong>PAN:</strong> {reviewData.pan_number || 'Not provided'}</div>
            <div><strong>Emergency Contact:</strong> {reviewData.emergency_contact_name}</div>
            <div><strong>Emergency Number:</strong> {reviewData.emergency_contact_number}</div>
            <div className="md:col-span-2"><strong>Special Requirements:</strong> {reviewData.special_requirements || 'None'}</div>
            <div><strong>Payment Method:</strong> {reviewData.payment_method || 'Not selected'}</div>
          </div>
          
          <div className="flex justify-end space-x-4">
            <button
              onClick={() => setShowReviewModal(false)}
              className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Back to Edit
            </button>
            <button
              onClick={confirmCustomerSubmission}
              disabled={loading}
              className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              {loading ? 'Submitting...' : 'Confirm & Submit'}
            </button>
          </div>
        </div>
      </div>
    )
  );

  const renderTourForm = () => (
    <div className="bg-white p-8 rounded-xl shadow-lg">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">Create New Tour</h2>
      <form onSubmit={handleTourSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Tour Name *</label>
            <input
              type="text"
              value={tourForm.name}
              onChange={(e) => setTourForm({...tourForm, name: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Destination *</label>
            <input
              type="text"
              value={tourForm.destination}
              onChange={(e) => setTourForm({...tourForm, destination: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Start Date *</label>
            <input
              type="date"
              value={tourForm.start_date}
              onChange={(e) => setTourForm({...tourForm, start_date: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">End Date *</label>
            <input
              type="date"
              value={tourForm.end_date}
              onChange={(e) => setTourForm({...tourForm, end_date: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Price (₹) *</label>
            <input
              type="number"
              value={tourForm.price}
              onChange={(e) => setTourForm({...tourForm, price: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Transport Mode *</label>
            <select
              value={tourForm.transport_mode}
              onChange={(e) => setTourForm({...tourForm, transport_mode: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              required
            >
              <option value="">Select Transport</option>
              <option value="Flight">Flight</option>
              <option value="Train">Train</option>
              <option value="Bus">Bus</option>
              <option value="Car">Car</option>
              <option value="Flight + Local Transport">Flight + Local Transport</option>
              <option value="Train + Local Transport">Train + Local Transport</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Max Capacity</label>
            <input
              type="number"
              value={tourForm.max_capacity}
              onChange={(e) => setTourForm({...tourForm, max_capacity: parseInt(e.target.value)})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              min="1"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Image URL (Optional)</label>
            <input
              type="url"
              value={tourForm.image_url}
              onChange={(e) => setTourForm({...tourForm, image_url: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="https://example.com/image.jpg"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">Description *</label>
            <textarea
              value={tourForm.description}
              onChange={(e) => setTourForm({...tourForm, description: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              rows="4"
              required
            />
          </div>
        </div>
        
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={loading}
            className="bg-green-600 text-white px-8 py-3 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
          >
            {loading ? 'Creating...' : 'Create Tour'}
          </button>
        </div>
      </form>
    </div>
  );

  const renderCustomersList = () => (
    <div className="bg-white rounded-xl shadow-lg">
      <div className="p-6 border-b border-gray-200 flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-800">Customer Management</h2>
        <div className="flex space-x-2">
          <button
            onClick={exportToPDF}
            className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
          >
            Export PDF
          </button>
          <button
            onClick={exportToCSV}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
          >
            Export CSV
          </button>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tour</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Contact</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Payment</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {customers.map((customer, index) => (
              <tr key={customer.customer_id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{customer.first_name} {customer.last_name}</div>
                  <div className="text-sm text-gray-500">{customer.email}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {tours.find(t => t.tour_id === customer.tour_id)?.name || 'Unknown Tour'}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">{customer.mobile}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    customer.payment_status === 'paid' ? 'bg-green-100 text-green-800' :
                    customer.payment_status === 'partial' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {customer.payment_status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button className="text-indigo-600 hover:text-indigo-900 mr-3">Edit</button>
                  <button className="text-red-600 hover:text-red-900">Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {customers.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No customers found. Add some customers to get started.
          </div>
        )}
      </div>
    </div>
  );

  const renderToursList = () => (
    <div className="bg-white rounded-xl shadow-lg">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-2xl font-bold text-gray-800">Tour Management</h2>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-6">
        {tours.map((tour) => (
          <div key={tour.tour_id} className="border border-gray-200 rounded-lg overflow-hidden hover:shadow-lg transition-shadow">
            {tour.image_url && (
              <img src={tour.image_url} alt={tour.name} className="w-full h-48 object-cover" />
            )}
            <div className="p-4">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">{tour.name}</h3>
              <p className="text-sm text-gray-600 mb-2">{tour.destination}</p>
              <p className="text-sm text-gray-500 mb-3">{tour.description.substring(0, 100)}...</p>
              <div className="flex justify-between items-center mb-2">
                <span className="text-2xl font-bold text-green-600">₹{tour.price.toLocaleString()}</span>
                <span className="text-sm text-gray-500">{tour.booked_count}/{tour.max_capacity} booked</span>
              </div>
              <div className="text-sm text-gray-500 mb-3">
                {new Date(tour.start_date).toLocaleDateString()} - {new Date(tour.end_date).toLocaleDateString()}
              </div>
              <div className="flex justify-between">
                <button className="text-blue-600 hover:text-blue-800 text-sm">Edit</button>
                <button className="text-red-600 hover:text-red-800 text-sm">Delete</button>
              </div>
            </div>
          </div>
        ))}
      </div>
      {tours.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No tours found. Create some tours to get started.
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <img 
                src="https://images.unsplash.com/photo-1506905925346-21bda4d32df4?q=80&w=100" 
                alt="निसर्ग भ्रमंती" 
                className="h-12 w-12 rounded-full mr-4"
              />
              <div>
                <h1 className="text-3xl font-bold text-gray-900">निसर्ग भ्रमंती</h1>
                <p className="text-sm text-gray-600">Nature Tours & Travel Management</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {[
              {key: 'dashboard', label: 'Dashboard'},
              {key: 'customer-form', label: 'Add Customer'},
              {key: 'customers', label: 'Customers'},
              {key: 'tour-form', label: 'Add Tour'},
              {key: 'tours', label: 'Tours'}
            ].map((item) => (
              <button
                key={item.key}
                onClick={() => setCurrentView(item.key)}
                className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors ${
                  currentView === item.key
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {currentView === 'dashboard' && renderDashboard()}
        {currentView === 'customer-form' && renderCustomerForm()}
        {currentView === 'customers' && renderCustomersList()}
        {currentView === 'tour-form' && renderTourForm()}
        {currentView === 'tours' && renderToursList()}
      </main>

      {/* Review Modal */}
      {renderReviewModal()}

      {/* Loading Overlay */}
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-25 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-xl">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading...</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;