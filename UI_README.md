# REST API Dashboard - User Interface

## Overview

A complete web-based UI dashboard has been implemented for your Flask REST API. The dashboard provides an intuitive interface for user management, authentication, and administration.

## Features

### For All Users
- **Home Page**: Welcome page with quick access to registration and login
- **User Registration**: Create new accounts with email validation and strong password requirements
- **User Login**: Secure login with JWT token-based authentication
- **Dashboard**: Personal dashboard after login
- **Profile Management**: Update username, email, and password
- **Account Deletion**: Option to delete your account (irreversible)

### For Administrators
- **User Management**: View all users in the system
- **Admin Controls**: Promote regular users to administrators
- **User Monitoring**: See user roles and email addresses

## File Structure

```
static/
├── index.html      # Main HTML structure and templates
├── styles.css      # Responsive styling and UI components
└── script.js       # Client-side logic and API communication
```

## How to Run

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Flask application**:
   ```bash
   python app.py
   ```

3. **Access the dashboard**:
   - Open your browser and go to: `http://localhost:5000`
   - The UI will load on the home page

## User Workflows

### Registration
1. Click "Get Started" or navigate to Register page
2. Enter username, email, and password
3. Password must contain:
   - At least one uppercase letter
   - At least one lowercase letter
   - At least one number
   - At least one special character
   - Minimum 8 characters
4. Submit to create account

### Login
1. Click "Sign In" or navigate to Login page
2. Enter username and password
3. Successfully logged-in users can access the dashboard

### Dashboard Features
- **View Profile**: See your username and role
- **Update Profile**: Change username, email, or password
- **Delete Account**: Permanently remove your account
- **Admin Panel** (if you're an admin):
  - View all users in a table
  - Promote users to administrators

## Technical Details

### Session Management
- Authentication tokens are stored in browser's localStorage
- Sessions persist across page reloads
- Login status is maintained until logout

### API Integration
The UI communicates with these API endpoints:
- `POST /register` - Create new user account
- `POST /login` - Authenticate user and get JWT token
- `GET /users` - Retrieve all users (admin only)
- `GET /users/<id>` - Get specific user details
- `PUT /users/<id>` - Update user information
- `DELETE /users/<id>` - Delete user account
- `POST /admin/promote/<id>` - Promote user to admin

### CORS Configuration
Flask-CORS has been enabled to allow cross-origin requests from the frontend to the API endpoints.

## Security Notes

1. **Password Security**: Passwords are validated on the frontend and hashed on the backend
2. **JWT Authentication**: All protected endpoints require a valid JWT token in the Authorization header
3. **Role-Based Access**: Admin endpoints check user role before allowing access
4. **HTTPS**: For production, always use HTTPS instead of HTTP

## Browser Compatibility

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers

## Customization

### Styling
Edit `static/styles.css` to customize:
- Color scheme
- Layout and spacing
- Responsive breakpoints
- Component styles

### Functionality
Edit `static/script.js` to modify:
- API endpoints
- Validation rules
- Error handling
- UI behavior

### HTML Structure
Edit `static/index.html` to:
- Add new pages/sections
- Change form fields
- Modify navigation

## Troubleshooting

### CORS Errors
If you see CORS errors in the browser console:
- Ensure Flask-CORS is installed: `pip install flask-cors`
- Make sure the API is running on `http://localhost:5000`

### Static Files Not Loading
- Verify the `static/` folder exists in the same directory as `app.py`
- Check that `index.html`, `styles.css`, and `script.js` are in the `static/` folder

### Login Issues
- Ensure your password meets the strength requirements
- Check that you've registered an account first
- Verify the API is running

## Future Enhancements

Possible improvements:
- Password reset functionality
- User profile pictures
- Email verification
- Two-factor authentication
- Activity logs
- Search and filtering for users
- Pagination for user lists
- Real-time notifications
