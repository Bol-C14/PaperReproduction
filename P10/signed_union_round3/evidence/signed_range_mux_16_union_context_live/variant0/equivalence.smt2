; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(assert
 (let ((?x550 ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) a))))))))
(let (($x30 (and (distinct (ite (bvsgt (_ bv0 16) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let (($x18 (and (distinct (ite (= (ite (bvsgt (_ bv65529 16) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x20 (ite (and (and (distinct (ite (bvsgt (_ bv8 16) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) $x18) (_ bv1 1) (_ bv0 1))))
(let (($x23 (and (distinct ?x20 (_ bv0 1)) true)))
(and (distinct (ite $x23 (ite $x30 (bvneg ((_ extract 15 0) a)) a) c) (ite $x23 ((_ extract 15 0) (ite $x30 (bvneg ((_ extract 15 0) ?x550)) ?x550)) c)) true)))))))
(check-sat)
