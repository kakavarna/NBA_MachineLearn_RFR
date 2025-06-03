SELECT
	p.game_id,
	opp.`date`,
	p.teamCode,
	opp.teamCode AS oppTeam,
	p.firstName,
	p.lastName,
	p.minutes,
	p.points,
	p.tpm,
	p.tpp,
	p.fgm,
	p.fgp,
	p.ftm,
	p.ftp,
	p.totReb,
	p.assists,
	p.steals,
	p.blocks,
	p.points+p.totReb+p.assists AS pra,
	p.points+p.assists AS pa,
	p.points+p.totReb AS pr,
	p.totReb+p.assists AS ra
FROM tbl_playerstats p
INNER JOIN tbl_games opp
ON opp.game_id = p.game_id AND opp.teamCode != p.teamCode
ORDER BY p.game_id desc