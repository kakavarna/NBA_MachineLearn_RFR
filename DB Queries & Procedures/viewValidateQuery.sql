SELECT
	pred.game_id,
	pred.date,
	pred.homeCode AS HOME,
	pred.visitorCode AS VISITOR,
	if(pred.homePlusMinus = 0, 'TIE',if(pred.homePlusMinus > 0,pred.homeCode,pred.visitorCode)) AS PredictedWinner,
	if(vt.homePlusMinus = 0, 'TIE',if(vt.homePlusMinus > 0,vt.homeCode,vt.visitorCode)) AS ActualWinner,
	if((if(pred.homePlusMinus = 0, 'TIE',if(pred.homePlusMinus > 0,pred.homeCode,pred.visitorCode)))=(if(vt.homePlusMinus = 0, 'TIE',if(vt.homePlusMinus > 0,vt.homeCode,vt.visitorCode))),
	 'HIT','') AS 'CorrectWinner?',
	pred.homePoints AS PredictedHOMEpoints,
	vt.homePoints AS ActualHOMEpoints,
	pred.visitorPoints AS PredictedVISITORpoints,
	vt.visitorPoints AS ActualVISITORpoints,
	(pred.homePlusMinus) AS PredPlusMinus,
	vt.homePlusMinus AS ActualPlusMinus,
	pred.totalPoints AS PredictedTOTALpoints,
	vt.totalPoints AS ActualTOTALpts,
	(vt.totalPoints-pred.totalPoints) AS TOTALptsDif,
	homeMLodds,
	visitorMLodds,
	if((pred.homePoints > pred.visitorPoints AND homeMLodds > visitorMLodds) OR (pred.visitorPoints > pred.homePoints AND visitorMLodds > homeMLodds),1,0) AS UnderdogPick
FROM tbl_predictions pred
LEFT JOIN view_train vt ON vt.GameID = pred.game_id
ORDER BY DATE desc, game_id desc