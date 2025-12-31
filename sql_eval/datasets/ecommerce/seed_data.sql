-- E-commerce Sample Seed Data
-- sql-eval bundled dataset

-- Customers
INSERT INTO customers (customer_id, name, email, city, state, country, created_at) VALUES
(1, 'Rahul Sharma', 'rahul.sharma@email.com', 'Mumbai', 'Maharashtra', 'India', '2023-01-15'),
(2, 'Priya Patel', 'priya.patel@email.com', 'Bangalore', 'Karnataka', 'India', '2023-02-20'),
(3, 'Amit Kumar', 'amit.kumar@email.com', 'Delhi', 'Delhi', 'India', '2023-03-10'),
(4, 'Sneha Reddy', 'sneha.reddy@email.com', 'Hyderabad', 'Telangana', 'India', '2023-04-05'),
(5, 'Vikram Singh', 'vikram.singh@email.com', 'Chennai', 'Tamil Nadu', 'India', '2023-05-12'),
(6, 'Ananya Gupta', 'ananya.gupta@email.com', 'Pune', 'Maharashtra', 'India', '2023-06-18'),
(7, 'Rajesh Nair', 'rajesh.nair@email.com', 'Kochi', 'Kerala', 'India', '2023-07-22'),
(8, 'Meera Iyer', 'meera.iyer@email.com', 'Bangalore', 'Karnataka', 'India', '2023-08-30'),
(9, 'Arjun Menon', 'arjun.menon@email.com', 'Mumbai', 'Maharashtra', 'India', '2023-09-14'),
(10, 'Kavita Joshi', 'kavita.joshi@email.com', 'Jaipur', 'Rajasthan', 'India', '2023-10-25');

-- Products
INSERT INTO products (product_id, name, category, subcategory, price, cost, stock_quantity, is_active) VALUES
(1, 'iPhone 15 Pro', 'Electronics', 'Smartphones', 134900.00, 95000.00, 50, 1),
(2, 'Samsung Galaxy S24', 'Electronics', 'Smartphones', 79999.00, 55000.00, 75, 1),
(3, 'MacBook Air M3', 'Electronics', 'Laptops', 114900.00, 80000.00, 30, 1),
(4, 'Sony WH-1000XM5', 'Electronics', 'Headphones', 29990.00, 18000.00, 100, 1),
(5, 'Nike Air Max 270', 'Fashion', 'Shoes', 12995.00, 7000.00, 200, 1),
(6, 'Levis 501 Jeans', 'Fashion', 'Clothing', 3999.00, 2000.00, 150, 1),
(7, 'Instant Pot Duo', 'Home', 'Kitchen', 9999.00, 5500.00, 80, 1),
(8, 'Dyson V15 Vacuum', 'Home', 'Appliances', 62900.00, 40000.00, 25, 1),
(9, 'Kindle Paperwhite', 'Electronics', 'E-readers', 14999.00, 9000.00, 120, 1),
(10, 'Apple Watch Series 9', 'Electronics', 'Wearables', 41900.00, 28000.00, 60, 1),
(11, 'Samsung 55" OLED TV', 'Electronics', 'TVs', 129990.00, 85000.00, 20, 1),
(12, 'Boat Rockerz 450', 'Electronics', 'Headphones', 1499.00, 800.00, 500, 1),
(13, 'Puma Running Shoes', 'Fashion', 'Shoes', 4999.00, 2500.00, 300, 1),
(14, 'Prestige Induction', 'Home', 'Kitchen', 2499.00, 1500.00, 150, 1),
(15, 'Canon EOS R50', 'Electronics', 'Cameras', 75990.00, 52000.00, 15, 1);

-- Orders
INSERT INTO orders (order_id, customer_id, order_date, status, total_amount, discount_amount, shipping_city, shipping_state) VALUES
(1, 1, '2024-01-05', 'delivered', 134900.00, 5000.00, 'Mumbai', 'Maharashtra'),
(2, 2, '2024-01-10', 'delivered', 29990.00, 0.00, 'Bangalore', 'Karnataka'),
(3, 3, '2024-01-15', 'delivered', 79999.00, 2000.00, 'Delhi', 'Delhi'),
(4, 1, '2024-02-01', 'delivered', 12995.00, 1000.00, 'Mumbai', 'Maharashtra'),
(5, 4, '2024-02-10', 'delivered', 114900.00, 5000.00, 'Hyderabad', 'Telangana'),
(6, 5, '2024-02-15', 'shipped', 41900.00, 0.00, 'Chennai', 'Tamil Nadu'),
(7, 2, '2024-02-20', 'delivered', 9999.00, 500.00, 'Bangalore', 'Karnataka'),
(8, 6, '2024-03-01', 'delivered', 3999.00, 0.00, 'Pune', 'Maharashtra'),
(9, 7, '2024-03-05', 'delivered', 62900.00, 3000.00, 'Kochi', 'Kerala'),
(10, 3, '2024-03-10', 'delivered', 14999.00, 0.00, 'Delhi', 'Delhi'),
(11, 8, '2024-03-15', 'shipped', 129990.00, 10000.00, 'Bangalore', 'Karnataka'),
(12, 9, '2024-03-20', 'delivered', 1499.00, 0.00, 'Mumbai', 'Maharashtra'),
(13, 10, '2024-04-01', 'pending', 4999.00, 0.00, 'Jaipur', 'Rajasthan'),
(14, 1, '2024-04-05', 'delivered', 75990.00, 5000.00, 'Mumbai', 'Maharashtra'),
(15, 2, '2024-04-10', 'delivered', 2499.00, 0.00, 'Bangalore', 'Karnataka'),
(16, 4, '2024-04-15', 'shipped', 29990.00, 1500.00, 'Hyderabad', 'Telangana'),
(17, 5, '2024-04-20', 'delivered', 79999.00, 4000.00, 'Chennai', 'Tamil Nadu'),
(18, 6, '2024-05-01', 'delivered', 12995.00, 0.00, 'Pune', 'Maharashtra'),
(19, 8, '2024-05-05', 'pending', 41900.00, 2000.00, 'Bangalore', 'Karnataka'),
(20, 9, '2024-05-10', 'delivered', 14999.00, 1000.00, 'Mumbai', 'Maharashtra');

-- Order Items
INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price, discount_percent) VALUES
(1, 1, 1, 1, 134900.00, 0),
(2, 2, 4, 1, 29990.00, 0),
(3, 3, 2, 1, 79999.00, 0),
(4, 4, 5, 1, 12995.00, 0),
(5, 5, 3, 1, 114900.00, 0),
(6, 6, 10, 1, 41900.00, 0),
(7, 7, 7, 1, 9999.00, 0),
(8, 8, 6, 1, 3999.00, 0),
(9, 9, 8, 1, 62900.00, 0),
(10, 10, 9, 1, 14999.00, 0),
(11, 11, 11, 1, 129990.00, 0),
(12, 12, 12, 1, 1499.00, 0),
(13, 13, 13, 1, 4999.00, 0),
(14, 14, 15, 1, 75990.00, 0),
(15, 15, 14, 1, 2499.00, 0),
(16, 16, 4, 1, 29990.00, 5),
(17, 17, 2, 1, 79999.00, 5),
(18, 18, 5, 1, 12995.00, 0),
(19, 19, 10, 1, 41900.00, 0),
(20, 20, 9, 1, 14999.00, 0),
(21, 1, 4, 1, 29990.00, 10),
(22, 5, 10, 1, 41900.00, 0),
(23, 14, 4, 1, 29990.00, 0);

-- Reviews
INSERT INTO reviews (review_id, product_id, customer_id, rating, review_text, created_at) VALUES
(1, 1, 1, 5, 'Amazing phone! Best camera I have ever used.', '2024-01-20'),
(2, 4, 2, 5, 'Best noise cancellation headphones. Worth every penny.', '2024-01-25'),
(3, 2, 3, 4, 'Great phone but battery could be better.', '2024-01-30'),
(4, 5, 1, 4, 'Very comfortable shoes for running.', '2024-02-15'),
(5, 3, 4, 5, 'MacBook Air is incredibly fast. Love it!', '2024-02-25'),
(6, 7, 2, 5, 'Makes cooking so easy. Highly recommend!', '2024-03-01'),
(7, 8, 7, 4, 'Powerful vacuum but quite expensive.', '2024-03-15'),
(8, 9, 3, 5, 'Perfect for reading. Battery lasts forever.', '2024-03-20'),
(9, 11, 8, 5, 'Picture quality is stunning!', '2024-03-25'),
(10, 12, 9, 3, 'Good for the price but sound quality is average.', '2024-03-28'),
(11, 15, 1, 5, 'Excellent camera for beginners and pros alike.', '2024-04-15'),
(12, 10, 5, 4, 'Great smartwatch but wish battery lasted longer.', '2024-04-20'),
(13, 2, 5, 5, 'Changed my mind after using it more. Great phone!', '2024-05-01'),
(14, 4, 4, 5, 'Second pair I bought. Addicted to the sound quality.', '2024-05-10'),
(15, 1, 9, 4, 'Expensive but worth it for the features.', '2024-05-15');
