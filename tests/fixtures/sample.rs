/// A simple Rust module for testing engspec generation.

/// Add two integers.
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}

/// Divide a by b. Returns Err if b is zero.
pub fn divide(a: f64, b: f64) -> Result<f64, String> {
    if b == 0.0 {
        return Err("Cannot divide by zero".to_string());
    }
    Ok(a / b)
}

/// A simple calculator.
pub struct Calculator {
    history: Vec<f64>,
}

impl Calculator {
    pub fn new() -> Self {
        Calculator {
            history: Vec::new(),
        }
    }

    /// Compute an operation and record the result.
    pub fn compute(&mut self, op: &str, a: f64, b: f64) -> Result<f64, String> {
        let result = match op {
            "add" => Ok(a + b),
            "div" => divide(a, b),
            _ => Err(format!("Unknown operation: {}", op)),
        }?;
        self.history.push(result);
        Ok(result)
    }
}
