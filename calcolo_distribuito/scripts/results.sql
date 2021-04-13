SELECT results.id, results.client, operations.operation, results.result 
FROM results 
JOIN operations 
ON results.operation == operations.id