WITH squaredErrors AS (
   SELECT 
   	POWER(p.homePoints - t.homePoints, 2) AS sqHomeError,
      POWER(p.visitorPoints - t.visitorPoints, 2) AS sqVisitorError,
      POWER(p.totalPoints - t.totalPoints, 2) AS sqTotalError,
      POWER(p.homePlusMinus - t.homePlusMinus, 2) AS sqPlusMinusError,
      p.date
   FROM tbl_predictions p
   INNER JOIN view_train t ON t.GameID = p.game_id
   ORDER BY DATE desc
   LIMIT 200
)
SELECT 
   'RMSE homePoints' AS metric, 
   ROUND(SQRT(SUM(sqHomeError) / COUNT(sqHomeError)), 2) AS value
FROM squaredErrors
UNION
SELECT 
   'RMSE visitorPoints' AS metric, 
   ROUND(SQRT(SUM(sqVisitorError) / COUNT(sqVisitorError)), 2) AS value
FROM squaredErrors
UNION
SELECT 
   'RMSE TotalPoints' AS metric, 
   ROUND(SQRT(SUM(sqTotalError) / COUNT(sqTotalError)), 2) AS value
FROM squaredErrors
UNION
SELECT 
   'RMSE PlusMinus' AS metric, 
   ROUND(SQRT(SUM(sqPlusMinusError) / COUNT(sqPlusMinusError)), 2) AS value
FROM squaredErrors
UNION
SELECT
	'Winner Misclassification Rate' AS metric,
	(WITH winners AS (SELECT CASE WHEN PredictedWinner != ActualWinner THEN 1 ELSE 0 END AS WRONG,
			date from view_validate 
			WHERE ActualWinner IS NOT NULL 
			ORDER BY DATE desc
			LIMIT 200
			)
		SELECT ROUND((SUM(WRONG))/COUNT(*)*100,2) AS RATE
		FROM winners) AS value