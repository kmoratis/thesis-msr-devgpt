// This is a sample JavaScript file with ESLint issues

function addNumbers(a, b) {
   // Missing semicolon at the end of the line
   const sum = a + b // No space before and after the operator
 
   // Unused variable
   const unusedVariable = 'This variable is not used'
 
   // Block with no braces
   if (a > 0)
     console.log('Positive') // This statement is not inside braces
 
   // Incorrect indentation
   console.log('This is not indented properly')
 
   // Undefined variable
   console.log(nonExistentVariable) // nonExistentVariable is not defined
 
   // Double equal sign instead of triple equal sign
   if (a == '5') {
     console.log('Equal')
   }
 
   // Using the 'eval' function
   const dangerousString = 'console.log("Hello, world!")'
   eval(dangerousString)
 
   // Unexpected console statement
   console.log('This should be removed before production')
 
   return sum
 }
 
 // Calling the function with too few arguments
 const result = addNumbers(5)
 
 // Arrow function with no parentheses for a single parameter
 const square = x => x * x
 
 // Template literal with no expression
 const greeting = `Hello, world!`
 
 // Unused import
 import { unusedImport } from 'some-module'
 
 // Function with too many parameters
 function tooManyParameters(a, b, c, d, e, f) {
   return a + b + c + d + e + f
 }
 
 // Object property shorthand
 const x = 10
 const y = 20
 const coordinates = { x, y }
 
 // Using var instead of let/const
 var oldVariable = 'I am outdated'
 
 // Dangling comma in the array
 const arrayWithComma = [1, 2, 3,]
 
 // Missing space before function parentheses
 function exampleFunction () {
   return 'This function has a space issue'
 }
 