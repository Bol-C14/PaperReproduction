; benchmark generated from python API
(set-info :status unknown)
(declare-fun a () (_ BitVec 8))
(assert
 (let (($x20 (and (distinct (ite (= (ite (bvsgt (_ bv253 8) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x22 (ite (and (and (distinct (ite (bvsgt (_ bv4 8) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) $x20) (_ bv1 1) (_ bv0 1))))
(let (($x6 (and true)))
(let (($x24 (and $x6 (and $x6 (and $x6)) (and (distinct ?x22 (_ bv0 1)) true))))
(let (($x31 (and $x24 true (and (distinct (_ bv1 1) ((_ extract 0 0) (ite (bvsgt (_ bv8 8) a) (_ bv1 1) (_ bv0 1)))) true))))
(or (and (distinct $x24 true) true) $x31)))))))
(check-sat)
