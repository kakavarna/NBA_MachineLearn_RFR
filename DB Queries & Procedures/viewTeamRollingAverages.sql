WITH RankedGames AS (
    SELECT 
        teamCode,
        game_id,
        date,
        points,
        totReb,
        fgm,
        fga,
        tpm,
        tpa,
        ftm,
        fta,
        assists,
        ROW_NUMBER() OVER (PARTITION BY teamCode ORDER BY date DESC) AS game_rank
    FROM tbl_games
)
SELECT 
    teamCode,
    AVG(points) AS AvgPts,
    AVG(totReb) AS AvgTotReb,
    AVG(fgm) AS AvgFGM,
    AVG(fga) AS AvgFGA,
    Round(AVG(fgm)/AVG(fga) * 100,2) AS AvgFGP,
    AVG(tpm) AS AvgTPM,
    AVG(tpa) AS AvgTPA,
    Round(AVG(tpm)/AVG(tpa) * 100,2) AS AvgTPP,
    AVG(ftm) AS AvgFTM,
    AVG(fta) AS AvgFTA,
    Round(AVG(ftm)/AVG(fta) * 100,2) AS AvgFTP,
    AVG(assists) AS AvgAssists
FROM RankedGames
WHERE game_rank <= 5
GROUP BY teamCode;
